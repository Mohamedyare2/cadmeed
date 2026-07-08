-- Create Projects Table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    name TEXT NOT NULL,
    client TEXT,
    city TEXT,
    description TEXT
);

-- Create Project Images Table (1 project has up to 10 images)
CREATE TABLE project_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL
);

-- NOTE: You will also need to create a Supabase Storage bucket named 'gallery'
-- Ensure RLS is configured appropriately if needed, or stick to server-side keys
