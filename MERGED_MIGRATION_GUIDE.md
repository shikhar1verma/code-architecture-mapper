# Merged Migration Guide

## 🔄 **Migration Consolidation**

I've merged both migration files into a single comprehensive schema for a cleaner database setup.

## 📁 **What Changed**

### **Before** (2 separate files):
```
backend/migrations/
├── 001_initial_schema.sql          # Basic tables
└── 002_add_intelligent_diagrams.sql # Added diagram columns
```

### **After** (1 unified file):
```
backend/migrations/
└── 001_initial_schema.sql          # Complete schema with intelligent diagrams
```

## 🗃️ **Complete Database Schema**

The merged `001_initial_schema.sql` now includes:

### **Core Tables**:
- ✅ `analyses` - Repository analysis results
- ✅ `files` - Individual file metrics  
- ✅ `examples` - Example repositories

### **Diagram Storage** (All in one place):
```sql
-- Original diagrams
mermaid_modules TEXT,         -- Basic dependency diagram
mermaid_folders TEXT,         -- Project structure

-- NEW: Intelligent dependency diagrams  
mermaid_modules_simple TEXT,   -- Overview mode
mermaid_modules_balanced TEXT, -- Grouped mode  
mermaid_modules_detailed TEXT  -- Detailed mode
```

## 🚀 **Fresh Database Setup**

### **1. Drop Existing Database** (if needed):
```bash
# Connect to PostgreSQL and drop the database
psql -U postgres -c "DROP DATABASE IF EXISTS repo_architect;"
```

### **2. Run Clean Setup**:
```bash
cd backend
python db_setup.py init
```

### **3. Verify Setup**:
```bash
# Check that all columns exist
psql -U postgres -d repo_architect -c "
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'analyses' 
AND column_name LIKE 'mermaid%'
ORDER BY column_name;
"
```

**Expected Output**:
```
column_name
------------------------
mermaid_folders
mermaid_modules
mermaid_modules_balanced
mermaid_modules_detailed
mermaid_modules_simple
```

## 🎯 **Benefits of Merged Migration**

1. **Simpler Setup** - Single migration file to run
2. **Cleaner History** - No migration dependencies
3. **Fresh Start** - Perfect for new database creation
4. **Complete Schema** - All features included from the start
5. **Better Documentation** - Clear column comments and organization

## 🔧 **Database Setup Commands**

### **Complete Fresh Setup**:
```bash
# 1. Navigate to backend
cd backend

# 2. Initialize database (creates DB + runs migration)
python db_setup.py init

# 3. Start your application
docker-compose up -d
```

### **Manual Setup** (if needed):
```bash
# 1. Create database only
python db_setup.py create-db

# 2. Run the unified migration
python db_setup.py run-migration 001_initial_schema.sql
```

## ✅ **Verification**

After setup, your database will have:
- ✅ All core tables (`analyses`, `files`, `examples`)
- ✅ All diagram columns (basic + intelligent)
- ✅ Proper indexes and constraints
- ✅ Example repositories pre-loaded
- ✅ Full documentation comments

## 🎉 **Result**

You now have a single, comprehensive migration that includes:
- 📊 **Complete Schema** - All tables and columns
- 🧠 **Intelligent Diagrams** - LLM-powered visualization support
- 🚀 **Clean Setup** - One command to rule them all
- 📝 **Full Documentation** - Clear column purposes

**Run `python db_setup.py init` and you're ready to go!** 🚀 