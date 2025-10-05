# LeadLedgerPro - Texas Home Services Lead Generation Platform

## Overview
LeadLedgerPro is a comprehensive lead generation platform designed to scrape public permit data from Texas sources and transform it into scored, actionable leads for home services contractors. The platform aims to provide a competitive edge in the home services market by automating lead discovery and qualification. It currently covers 6 major Texas metro areas, encompassing 11.6 million people, and features a Next.js dashboard for lead visualization, filtering, and export.

## User Preferences
- Clean, organized code structure
- Separate components for maintainability
- TypeScript for type safety
- Minimal temporary/debug files
- Navy blue and grey color theme for better readability (not vibrant colors)

## System Architecture
The platform utilizes a Next.js frontend with TypeScript for a responsive dashboard, connected to a Supabase PostgreSQL backend for data management.

### UI/UX Decisions
The dashboard features a navy blue and grey color scheme for a professional and readable interface. It includes components for regional selection, lead display, and an "Export CSV" function. Lead scoring is visually represented, categorizing leads as Hot, Warm, or Cold based on project value, recency, and other factors.

### Technical Implementations
- **Frontend**: Built with Next.js and TypeScript, serving a client-side dashboard for lead interaction. Authentication is currently disabled for streamlined access.
- **Backend & Data Ingestion**: Automated ingestion scripts, written in TypeScript, regularly scrape permit data from various Texas city and county sources (e.g., Houston, Dallas, Austin, Fort Worth, San Antonio, El Paso). These scripts process the raw data, separate owner and contractor information, assign lead types, and apply a lead scoring algorithm before storing them in Supabase.
- **API Routes**: Dedicated API endpoints handle regional data ingestion, provide real-time dashboard statistics (active counties, total leads, qualified leads), and facilitate CSV exports.
- **Scheduled Service**: A scheduled service runs every six hours to ensure the continuous ingestion of new permit data.
- **Database Schema**: The Supabase PostgreSQL database includes `permits` (raw data) and `leads` (processed and scored leads) tables. Key fields include `external_permit_id`, `name`, `owner_name`, `contractor_name`, `lead_type`, `trade`, `county`, `status`, `value`, `lead_score`, `address`, `phone`, and `email`.

### Feature Specifications
- **Multi-region Support**: Covers 6 major Texas metro areas, with plans for expansion.
- **Lead Scoring**: Leads are automatically scored (Hot/Warm/Cold) based on project value, permit recency, trade type, and location.
- **Owner/Contractor Separation**: Ingestion scripts prioritize owner names for higher-value leads and identify lead types (owner, contractor, unknown).
- **Real-time Statistics**: The homepage displays live statistics fetched from the Supabase database.
- **CSV Export**: Users can export filtered leads directly from the dashboard.
- **County/Region Mapping**: A system maps city names to their respective counties for data organization and filtering.

## External Dependencies
- **Supabase (PostgreSQL)**: The primary database and backend-as-a-service, used for storing permit and lead data, and providing API access.
- **Clearbit, Hunter.io, Apollo.io, ZoomInfo (Planned)**: These are potential third-party contact enrichment services identified for future integration to add phone numbers and email addresses to leads. The platform has `phone` and `email` fields ready in the database for this purpose.