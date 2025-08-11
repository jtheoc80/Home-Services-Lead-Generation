// Example usage of Lead TypeScript interfaces

import { Lead, LeadInsert, LeadUpdate } from './supabase';

// Example: Creating a new lead for insertion
const newLead: LeadInsert = {
  source: 'web_form',
  name: 'John Doe',
  phone: '555-123-4567',
  email: 'john.doe@example.com',
  address: '123 Main St',
  city: 'Houston',
  state: 'TX',
  zip: '77001',
  status: 'new'
};

// Example: Working with a lead returned from the database
function processLead(lead: Lead) {
  console.log(`Processing lead ${lead.id} for ${lead.name || 'unknown'}`);
  console.log(`Contact: ${lead.phone || lead.email || 'no contact info'}`);
  console.log(`Location: ${lead.city}, ${lead.state} ${lead.zip}`);
  console.log(`Created: ${lead.created_at}`);
}

// Example: Updating an existing lead
const leadUpdate: LeadUpdate = {
  status: 'contacted',
  phone: '555-987-6543' // Update phone number
};

export { newLead, processLead, leadUpdate };