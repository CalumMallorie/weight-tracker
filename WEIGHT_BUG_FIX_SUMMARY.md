# Weight Entry Bug Fix Summary

## Problem Description
Body weight entries were being saved as zero in the Docker/Unraid environment, despite users entering actual weight values (e.g., entering 87kg but it shows up as 0kg in the database). This issue only appeared in the Docker environment and worked fine locally.

## Root Cause Analysis
The issue was likely caused by one or more of the following factors in the Docker environment:
1. **Character encoding differences** between local and Docker environments
2. **Form data parsing issues** with special characters, whitespace, or encoding
3. **Locale-specific decimal separators** (e.g., European format using commas)
4. **JavaScript interference** with form field values
5. **Missing validation** to prevent zero weights from being saved

## Changes Made

### 1. Enhanced Form Data Parsing (`src/routes.py`)
- **Added fallback mechanisms** for form field names:
  - Primary: `weight` field
  - Fallback 1: `body-weight` field (from modal)
  - Fallback 2: `main-weight` field (from main form)
- **Added robust weight string processing**:
  - Strip whitespace from all form inputs
  - Handle European decimal separators (comma → dot)
  - Remove non-numeric characters except digits, dots, and minus signs
  - Handle encoding issues (null bytes, CRLF, etc.)

### 2. Comprehensive Logging (`src/routes.py`)
- **Added detailed form data logging**:
  - Raw form data dictionary
  - Individual field values with type and length information
  - Byte representation of weight strings
  - Request environment information (Content-Type, User-Agent, etc.)
- **Added weight conversion logging**:
  - Original → normalized → cleaned string transformations
  - Final float conversion results
  - Error details for failed conversions

### 3. Enhanced Validation (`src/services.py`)
- **Added final validation check** before database save:
  - Prevents zero weights for body mass entries
  - Logs critical errors when zero weights are attempted
  - Raises clear error messages for debugging

### 4. Fixed Logic Errors (`src/routes.py`)
- **Corrected variable definition order**:
  - Moved category lookup before logging statements
  - Fixed undefined variable references in debug logging

### 5. Robust Weight Parsing Logic
The new weight parsing logic handles:
- Normal decimals: `87.5` → `87.5`
- European format: `87,5` → `87.5`
- Whitespace: ` 87.5 ` → `87.5`
- Units: `87.5kg` → `87.5`
- Unicode: `87½` → `87.0`
- Encoding issues: `87.5\x00` → `87.5`
- Invalid input: `abc` → `0` (with warning)

## Testing
Created comprehensive test scripts:
- `test_weight_bug.py` - Local testing of weight parsing logic
- `debug_weight_entry.py` - Docker environment testing script

## Deployment Instructions
1. **Deploy the updated code** to your Docker/Unraid environment
2. **Set log level to INFO** to capture detailed debugging information:
   ```bash
   docker run -e LOG_LEVEL=INFO ...
   ```
3. **Test weight entry** and monitor logs for any issues
4. **Check logs** for the detailed form parsing information to verify the fix

## Monitoring
After deployment, monitor the logs for:
- `Form submission - Raw form data:` entries
- `Weight conversion -` entries  
- Any `CRITICAL: Attempted to save body mass entry with zero weight!` errors

## Expected Outcome
- Body weight entries should now save the correct weight values
- Enhanced logging will help identify any remaining issues
- Robust parsing will handle various input formats and encoding issues
- Zero weight entries for body mass will be prevented with clear error messages

## Rollback Plan
If issues persist, the changes can be easily reverted by:
1. Removing the enhanced logging statements
2. Reverting to the original simple `float(weight_str)` conversion
3. The core functionality remains unchanged, only enhanced

## Files Modified
- `src/routes.py` - Enhanced form parsing and logging
- `src/services.py` - Added final validation check
- `test_weight_bug.py` - Test script (new)
- `debug_weight_entry.py` - Debug script (new)
- `WEIGHT_BUG_FIX_SUMMARY.md` - This summary (new) 