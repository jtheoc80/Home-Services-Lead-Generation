import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-agent-secret',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
}

interface EventRecord {
  id: string
  type: string
  payload: any
  created_at: string
}

interface GitHubCommentRequest {
  issue_number: number
  body: string
}

interface GitHubRepositoryDispatchRequest {
  event_type: string
  client_payload: any
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Verify X-Agent-Secret header
    const agentSecret = req.headers.get('x-agent-secret')
    const expectedSecret = Deno.env.get('AGENT_SECRET')
    
    if (!expectedSecret) {
      console.error('AGENT_SECRET environment variable not configured')
      return new Response(
        JSON.stringify({ error: 'Agent secret not configured on server' }),
        { 
          status: 503, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    if (!agentSecret) {
      return new Response(
        JSON.stringify({ error: 'X-Agent-Secret header required' }),
        { 
          status: 401, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    if (agentSecret !== expectedSecret) {
      return new Response(
        JSON.stringify({ error: 'Invalid agent secret' }),
        { 
          status: 401, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Only allow POST requests
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }),
        { 
          status: 405, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Get GitHub configuration
    const githubToken = Deno.env.get('GITHUB_TOKEN')
    const githubRepo = Deno.env.get('GITHUB_REPOSITORY') // format: owner/repo
    const githubIssueNumber = Deno.env.get('GITHUB_TRACKING_ISSUE_NUMBER') // optional
    
    if (!githubToken || !githubRepo) {
      return new Response(
        JSON.stringify({ error: 'GitHub configuration missing (GITHUB_TOKEN, GITHUB_REPOSITORY required)' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    console.log('GitHub Agent starting...')

    // 1. Fetch undelivered events from outbox
    const { data: events, error: fetchError } = await supabase
      .from('event_outbox')
      .select('*')
      .is('delivered_at', null)
      .order('created_at', { ascending: true })
      .limit(50) // Process in batches

    if (fetchError) {
      console.error('Error fetching events:', fetchError)
      return new Response(
        JSON.stringify({ error: 'Failed to fetch events', details: fetchError.message }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    if (!events || events.length === 0) {
      console.log('No pending events to process')
      return new Response(
        JSON.stringify({ 
          message: 'No pending events', 
          processed: 0,
          timestamp: new Date().toISOString()
        }),
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    console.log(`Processing ${events.length} events`)

    const processedEvents: string[] = []
    const errors: string[] = []

    // 2. Process each event
    for (const event of events as EventRecord[]) {
      try {
        let githubSuccess = false

        if (githubIssueNumber) {
          // Post comment to tracking issue
          githubSuccess = await postIssueComment(githubToken, githubRepo, parseInt(githubIssueNumber), event)
        } else {
          // Send repository dispatch event
          githubSuccess = await sendRepositoryDispatch(githubToken, githubRepo, event)
        }

        if (githubSuccess) {
          processedEvents.push(event.id)
        } else {
          errors.push(`Failed to process event ${event.id}`)
        }
      } catch (error) {
        console.error(`Error processing event ${event.id}:`, error)
        errors.push(`Error processing event ${event.id}: ${error.message}`)
      }
    }

    // 3. Mark successfully processed events as delivered
    if (processedEvents.length > 0) {
      const { error: updateError } = await supabase
        .rpc('mark_events_delivered', { event_ids: processedEvents })

      if (updateError) {
        console.error('Error marking events as delivered:', updateError)
        errors.push(`Failed to mark ${processedEvents.length} events as delivered`)
      } else {
        console.log(`Marked ${processedEvents.length} events as delivered`)
      }
    }

    // 4. Return results
    const result = {
      processed: processedEvents.length,
      errors: errors.length,
      total_events: events.length,
      error_details: errors.length > 0 ? errors : undefined,
      timestamp: new Date().toISOString()
    }

    console.log('GitHub Agent completed:', result)

    return new Response(
      JSON.stringify(result),
      { 
        status: errors.length > 0 ? 207 : 200, // 207 Multi-Status if there were errors
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('GitHub Agent error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error', 
        details: error.message,
        timestamp: new Date().toISOString()
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

async function postIssueComment(
  githubToken: string, 
  githubRepo: string, 
  issueNumber: number, 
  event: EventRecord
): Promise<boolean> {
  try {
    const commentBody = formatEventAsComment(event)
    
    const response = await fetch(`https://api.github.com/repos/${githubRepo}/issues/${issueNumber}/comments`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'Supabase-GH-Agent'
      },
      body: JSON.stringify({
        body: commentBody
      })
    })

    if (!response.ok) {
      console.error(`GitHub API error: ${response.status} ${response.statusText}`)
      const errorBody = await response.text()
      console.error('Error response:', errorBody)
      return false
    }

    console.log(`Posted comment for event ${event.id} to issue #${issueNumber}`)
    return true
  } catch (error) {
    console.error('Error posting issue comment:', error)
    return false
  }
}

async function sendRepositoryDispatch(
  githubToken: string, 
  githubRepo: string, 
  event: EventRecord
): Promise<boolean> {
  try {
    const eventType = event.type.replace('.', '_') // GitHub event types can't contain dots
    
    const response = await fetch(`https://api.github.com/repos/${githubRepo}/dispatches`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'Supabase-GH-Agent'
      },
      body: JSON.stringify({
        event_type: eventType,
        client_payload: {
          event_id: event.id,
          event_type: event.type,
          payload: event.payload,
          created_at: event.created_at
        }
      })
    })

    if (!response.ok) {
      console.error(`GitHub API error: ${response.status} ${response.statusText}`)
      const errorBody = await response.text()
      console.error('Error response:', errorBody)
      return false
    }

    console.log(`Sent repository dispatch for event ${event.id} with type ${eventType}`)
    return true
  } catch (error) {
    console.error('Error sending repository dispatch:', error)
    return false
  }
}

function formatEventAsComment(event: EventRecord): string {
  const timestamp = new Date(event.created_at).toLocaleString()
  
  switch (event.type) {
    case 'permit.created':
      return `🏗️ **New Permit Created** (${timestamp})

**Permit ID:** ${event.payload.permit_id}
**Address:** ${event.payload.address}
**City:** ${event.payload.city}, ${event.payload.county}
**Type:** ${event.payload.permit_type}
**Status:** ${event.payload.status}
**Applicant:** ${event.payload.applicant_name || 'N/A'}
**Contractor:** ${event.payload.contractor_name || 'N/A'}
**Valuation:** ${event.payload.valuation ? '$' + event.payload.valuation.toLocaleString() : 'N/A'}

*Event ID: ${event.id}*`

    case 'lead.created':
      return `👤 **New Lead Created** (${timestamp})

**Name:** ${event.payload.name || 'N/A'}
**Email:** ${event.payload.email || 'N/A'}
**Phone:** ${event.payload.phone || 'N/A'}
**Source:** ${event.payload.source || 'N/A'}
**Status:** ${event.payload.status || 'N/A'}

*Event ID: ${event.id}*`

    default:
      return `📋 **Event: ${event.type}** (${timestamp})

\`\`\`json
${JSON.stringify(event.payload, null, 2)}
\`\`\`

*Event ID: ${event.id}*`
  }
}

/* To deploy this function:
1. Save this file as supabase/functions/gh-agent/index.ts
2. Deploy with: supabase functions deploy gh-agent
3. Set environment variables:
   - AGENT_SECRET: Secret for authenticating requests
   - GITHUB_TOKEN: GitHub personal access token with repo permissions
   - GITHUB_REPOSITORY: Repository in format "owner/repo"
   - GITHUB_TRACKING_ISSUE_NUMBER: (optional) Issue number for comments
4. Invoke with: curl -X POST <function-url> -H "x-agent-secret: <secret>"
*/