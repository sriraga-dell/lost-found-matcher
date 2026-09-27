# Test Cases

## Test Case 1: User Registration

**Test:** Register a new user

**Input:**
- Name: Test User
- Email: test@example.com
- Password: test123

**Expected Result:**
User account should be created successfully.

**Status:** Pass


## Test Case 2: User Login

**Test:** Login with registered user

**Input:**
- Email: test@example.com
- Password: test123

**Expected Result:**
User should be redirected to the dashboard.

**Status:** Pass


## Test Case 3: Lost Item Registration

**Test:** Register a lost item

**Input:**
- Item Name: Black Wireless Earbuds
- Category: Electronics
- Location: Metro Station
- Date: 2026-09-15

**Expected Result:**
Lost report should be stored and assigned a report ID.

**Status:** Pass


## Test Case 4: Found Item Registration

**Test:** Register a found item

**Input:**
- Item Name: Black Wireless Earbuds Case
- Category: Electronics
- Location: Metro Station
- Date: 2026-09-15

**Expected Result:**
Found report should be stored and assigned a report ID.

**Status:** Pass


## Test Case 5: Required Field Validation

**Test:** Submit a report without required fields.

**Input:**
Leave one or more required fields empty.

**Expected Result:**
The report should not be submitted.

**Status:** Pass


## Test Case 6: Date Validation

**Test:** Enter an invalid date.

**Input:**
Invalid date format.

**Expected Result:**
The report should not be submitted.

**Status:** Pass


## Test Case 7: Search by Category

**Test:** Search reports using category.

**Input:**
Category: Electronics

**Expected Result:**
Electronics-related reports should be displayed.

**Status:** Pass


## Test Case 8: Search by Location

**Test:** Search reports using location.

**Input:**
Location: Metro Station

**Expected Result:**
Reports from the selected location should be displayed.

**Status:** Pass


## Test Case 9: Smart Matching

**Test:** Match a lost item with a similar found item.

**Input:**
Lost: Black wireless earbuds  
Found: Black wireless earbuds case

**Expected Result:**
A possible match should be displayed with a match percentage.

**Status:** Pass


## Test Case 10: Status Update

**Test:** Change report status.

**Input:**
Change status from Open to Matched or Returned.

**Expected Result:**
The selected status should be saved successfully.

**Status:** Pass


## Test Case 11: Open Reports

**Test:** View all open reports.

**Input:**
Open Reports page.

**Expected Result:**
Reports with Open status should be displayed.

**Status:** Pass


## Test Case 12: Image Upload

**Test:** Upload an image with a lost/found report.

**Input:**
PNG/JPG image.

**Expected Result:**
The image should be stored and displayed with the report.

**Status:** Pass
