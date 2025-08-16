'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';
import { getSupabaseClient } from './supabaseServer';
import type { LeadInsert } from '../../types/supabase';

// Zod schema for lead validation
const createLeadSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Valid email is required'),
  phone: z.string().min(1, 'Phone is required'),
  source: z.string().min(1, 'Source is required'),
  address: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  zip: z.string().optional(),
  service: z.string().optional(),
  county: z.string().optional()
});

export type CreateLeadInput = z.infer<typeof createLeadSchema>;

export interface CreateLeadResult {
  success: boolean;
  error?: string;
  leadId?: string;
}

/**
 * Server Action to create a new lead in Supabase
 * Uses service role in dev mode to bypass RLS
 */
export async function createLead(data: CreateLeadInput): Promise<CreateLeadResult> {
  try {
    // Validate input data
    const validatedData = createLeadSchema.parse(data);
    
    // Create lead payload
    const leadPayload: LeadInsert = {
      name: validatedData.name,
      email: validatedData.email,
      phone: validatedData.phone,
      source: validatedData.source,
      address: validatedData.address,
      city: validatedData.city,
      state: validatedData.state,
      zip: validatedData.zip,
      service: validatedData.service,
      county: validatedData.county,
      status: 'new'
    };

    // Get Supabase client with service role for dev mode
    const supabase = getSupabaseClient({ useServiceRole: true });
    
    // Insert lead into database
    const { data: insertedLead, error } = await supabase
      .from('leads')
      .insert([leadPayload])
      .select('id')
      .single();
    
    if (error) {
      console.error('Database insertion failed:', error);
      return {
        success: false,
        error: `Failed to create lead: ${error.message}`
      };
    }

    // Revalidate pages that show leads data
    revalidatePath('/dashboard');
    revalidatePath('/leads');
    revalidatePath('/leads/new');

    return {
      success: true,
      leadId: insertedLead.id
    };

  } catch (error) {
    console.error('Create lead action failed:', error);
    
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: `Validation failed: ${error.issues.map(i => i.message).join(', ')}`
      };
    }

    return {
      success: false,
      error: 'An unexpected error occurred while creating the lead'
    };
  }
}

/**
 * Server Action to create a lead and redirect to success page
 */
export async function createLeadAndRedirect(formData: FormData): Promise<void> {
  const data: CreateLeadInput = {
    name: formData.get('name') as string,
    email: formData.get('email') as string,
    phone: formData.get('phone') as string,
    source: formData.get('source') as string || 'website',
    address: formData.get('address') as string || undefined,
    city: formData.get('city') as string || undefined,
    state: formData.get('state') as string || undefined,
    zip: formData.get('zip') as string || undefined,
    service: formData.get('service') as string || undefined,
    county: formData.get('county') as string || undefined
  };

  const result = await createLead(data);
  
  if (result.success) {
    redirect('/leads?success=true');
  } else {
    // For Server Actions with redirect, we need to handle errors differently
    // In a real app, you might want to use cookies or searchParams to pass error state
    console.error('Lead creation failed:', result.error);
    redirect('/leads/new?error=' + encodeURIComponent(result.error || 'Unknown error'));
  }
}