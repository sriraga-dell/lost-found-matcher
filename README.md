# Lost & Found Matcher

## Project Overview

Lost & Found Matcher is a web-based application that helps users report lost and found items and identify possible matches.

The system compares item names, categories, locations, and descriptions to suggest possible matches with a confidence score.

## Features

- User registration
- User login
- Forgot password
- Lost item registration
- Found item registration
- Image upload
- Required field validation
- Date validation
- Search by category
- Search by location
- Smart fuzzy matching
- Match confidence percentage
- Possible / Strong / Very Strong match labels
- Open, Matched and Returned status
- Personal dashboard
- Open reports
- SQLite database
- Responsive web interface

## Matching System

The application calculates a match score using:

- Item Name – 40%
- Category – 25%
- Location – 20%
- Description – 15%

Total:

**100%**

### Match Levels

- 90% and above – Very Strong Match
- 75% to 89% – Strong Match
- 50% to 74% – Possible Match

The matching result is only a suggestion and does not guarantee that two reports belong to the same item.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- Jinja2
- Werkzeug
- Python difflib

## Project Structure

```text
lost-found matcher/
│
├── app.py
├── README.md
├── requirements.txt
├── sample_data.json
├── test_cases.md
├── .gitignore
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── forgot_password.html
│   ├── dashboard.html
│   ├── matches.html
│   └── open_reports.html
│
└── static/
    ├── style.css
    └── uploads/
    