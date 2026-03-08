"""
CV Templates - Professional, ATS-friendly designs
NO AI SLOP - Just clean, effective layouts
"""

TEMPLATES = {
    "modern": {
        "name": "Modern Professional",
        "description": "Clean, contemporary design. Best for tech, startups, creative roles.",
        "is_premium": False,
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 40px; }
        .header { border-bottom: 3px solid #2563eb; padding-bottom: 20px; margin-bottom: 25px; }
        .name { font-size: 32px; font-weight: 700; color: #1e40af; margin-bottom: 8px; }
        .contact { font-size: 14px; color: #666; }
        .contact span { margin-right: 15px; }
        .section { margin-bottom: 25px; }
        .section-title { font-size: 18px; font-weight: 600; color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px; }
        .summary { font-size: 15px; color: #444; text-align: justify; }
        .position { margin-bottom: 20px; }
        .position-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .position-title { font-weight: 600; font-size: 16px; color: #1f2937; }
        .company { color: #2563eb; }
        .date { color: #6b7280; font-size: 14px; }
        .description { font-size: 14px; color: #4b5563; margin-top: 8px; }
        .description ul { margin-left: 20px; }
        .description li { margin-bottom: 6px; }
        .skills-grid { display: flex; flex-wrap: wrap; gap: 8px; }
        .skill-tag { background: #eff6ff; color: #1e40af; padding: 6px 14px; border-radius: 4px; font-size: 14px; font-weight: 500; }
        .education-item { margin-bottom: 15px; }
        .education-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .degree { font-weight: 600; font-size: 15px; }
        .institution { color: #4b5563; }
        .year { color: #6b7280; font-size: 14px; }
        @media print { body { padding: 20px; } @page { margin: 1.5cm; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="name">{{full_name}}</div>
        <div class="contact">
            {{#email}}<span>📧 {{email}}</span>{{/email}}
            {{#phone}}<span>📱 {{phone}}</span>{{/phone}}
            {{#location}}<span>📍 {{location}}</span>{{/location}}
            {{#linkedin_url}}<span>💼 <a href="{{linkedin_url}}" style="color:#666;text-decoration:none;">LinkedIn</a></span>{{/linkedin_url}}
        </div>
    </div>

    {{#summary}}
    <div class="section">
        <div class="section-title">Professional Summary</div>
        <div class="summary">{{summary}}</div>
    </div>
    {{/summary}}

    {{#experience}}
    <div class="section">
        <div class="section-title">Experience</div>
        {{#.}}
        <div class="position">
            <div class="position-header">
                <div>
                    <span class="position-title">{{role}}</span>
                    {{#company}}<span class="company"> | {{company}}</span>{{/company}}
                </div>
                <div class="date">{{start_date}} - {{end_date}}</div>
            </div>
            {{#description}}
            <div class="description">{{description}}</div>
            {{/description}}
        </div>
        {{/.}}
    </div>
    {{/experience}}

    {{#education}}
    <div class="section">
        <div class="section-title">Education</div>
        {{#.}}
        <div class="education-item">
            <div class="education-header">
                <div>
                    <span class="degree">{{degree}}</span>
                    {{#field}}<span class="institution"> | {{field}}</span>{{/field}}
                    {{#institution}}<span class="institution"> | {{institution}}</span>{{/institution}}
                </div>
                <div class="year">{{graduation_year}}</div>
            </div>
        </div>
        {{/.}}
    </div>
    {{/education}}

    {{#skills}}
    <div class="section">
        <div class="section-title">Skills</div>
        <div class="skills-grid">
            {{#.}}<span class="skill-tag">{{.}}</span>{{/.}}
        </div>
    </div>
    {{/skills}}

    {{#certifications}}
    <div class="section">
        <div class="section-title">Certifications</div>
        {{#.}}
        <div class="education-item">
            <div class="education-header">
                <span class="degree">{{name}}</span>
                {{#issuer}}<span class="institution"> | {{issuer}}</span>{{/issuer}}
                {{#year}}<span class="year">{{year}}</span>{{/year}}
            </div>
        </div>
        {{/.}}
    </div>
    {{/certifications}}
</body>
</html>
        """,
    },
    
    "classic": {
        "name": "Classic Professional",
        "description": "Traditional, conservative design. Best for finance, law, corporate roles.",
        "is_premium": False,
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Georgia', 'Times New Roman', serif; line-height: 1.6; color: #000; max-width: 800px; margin: 0 auto; padding: 50px; }
        .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 15px; margin-bottom: 25px; }
        .name { font-size: 28px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; }
        .contact { font-size: 13px; }
        .contact span { margin: 0 10px; }
        .section { margin-bottom: 25px; }
        .section-title { font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #000; padding-bottom: 5px; margin-bottom: 15px; }
        .summary { font-size: 14px; text-align: justify; }
        .position { margin-bottom: 20px; }
        .position-header { margin-bottom: 5px; }
        .position-title { font-weight: 700; font-size: 15px; }
        .company { font-style: italic; }
        .date { float: right; font-size: 13px; }
        .description { font-size: 14px; clear: both; }
        .description ul { margin-left: 20px; }
        .description li { margin-bottom: 5px; }
        .skills-list { font-size: 14px; }
        .skills-list span { margin-right: 15px; }
        .education-item { margin-bottom: 12px; }
        .degree { font-weight: 700; font-size: 14px; }
        .institution { font-style: italic; }
        .year { float: right; font-size: 13px; }
        @media print { body { padding: 30px; } @page { margin: 2cm; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="name">{{full_name}}</div>
        <div class="contact">
            {{#email}}<span>{{email}}</span>{{/email}}
            {{#phone}}<span>{{phone}}</span>{{/phone}}
            {{#location}}<span>{{location}}</span>{{/location}}
            {{#linkedin_url}}<span>{{linkedin_url}}</span>{{/linkedin_url}}
        </div>
    </div>

    {{#summary}}
    <div class="section">
        <div class="section-title">Profile</div>
        <div class="summary">{{summary}}</div>
    </div>
    {{/summary}}

    {{#experience}}
    <div class="section">
        <div class="section-title">Professional Experience</div>
        {{#.}}
        <div class="position">
            <div class="position-header">
                <span class="position-title">{{role}}</span>
                <span class="date">{{start_date}} – {{end_date}}</span>
            </div>
            <div class="company">{{company}}</div>
            {{#description}}
            <div class="description">{{description}}</div>
            {{/description}}
        </div>
        {{/.}}
    </div>
    {{/experience}}

    {{#education}}
    <div class="section">
        <div class="section-title">Education</div>
        {{#.}}
        <div class="education-item">
            <span class="degree">{{degree}}</span>
            <span class="institution">{{institution}}</span>
            <span class="year">{{graduation_year}}</span>
        </div>
        {{/.}}
    </div>
    {{/education}}

    {{#skills}}
    <div class="section">
        <div class="section-title">Skills</div>
        <div class="skills-list">
            {{#.}}<span>{{.}}</span>{{/.}}
        </div>
    </div>
    {{/skills}}
</body>
</html>
        """,
    },
    
    "minimal": {
        "name": "Minimalist",
        "description": "Ultra-clean, simple design. Best for developers, designers, modern companies.",
        "is_premium": False,
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 750px; margin: 0 auto; padding: 60px 40px; }
        .header { margin-bottom: 40px; }
        .name { font-size: 36px; font-weight: 300; letter-spacing: -0.5px; margin-bottom: 12px; }
        .contact { font-size: 13px; color: #666; }
        .contact span { margin-right: 20px; }
        .section { margin-bottom: 35px; }
        .section-title { font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #666; margin-bottom: 20px; }
        .summary { font-size: 15px; color: #444; max-width: 600px; }
        .position { margin-bottom: 25px; }
        .position-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
        .position-title { font-size: 16px; font-weight: 500; }
        .company { color: #666; margin-left: 8px; }
        .date { font-size: 13px; color: #999; }
        .description { font-size: 14px; color: #555; }
        .description ul { margin-left: 18px; }
        .description li { margin-bottom: 8px; }
        .skills-grid { display: flex; flex-wrap: wrap; gap: 10px; }
        .skill-tag { font-size: 13px; color: #333; border: 1px solid #ddd; padding: 6px 12px; border-radius: 3px; }
        .education-item { margin-bottom: 15px; }
        .education-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .degree { font-size: 15px; font-weight: 500; }
        .institution { color: #666; margin-left: 8px; }
        .year { font-size: 13px; color: #999; }
        @media print { body { padding: 40px 30px; } @page { margin: 1.5cm; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="name">{{full_name}}</div>
        <div class="contact">
            {{#email}}<span>{{email}}</span>{{/email}}
            {{#phone}}<span>{{phone}}</span>{{/phone}}
            {{#location}}<span>{{location}}</span>{{/location}}
            {{#linkedin_url}}<span>{{linkedin_url}}</span>{{/linkedin_url}}
        </div>
    </div>

    {{#summary}}
    <div class="section">
        <div class="section-title">About</div>
        <div class="summary">{{summary}}</div>
    </div>
    {{/summary}}

    {{#experience}}
    <div class="section">
        <div class="section-title">Experience</div>
        {{#.}}
        <div class="position">
            <div class="position-header">
                <div>
                    <span class="position-title">{{role}}</span>
                    <span class="company">{{company}}</span>
                </div>
                <span class="date">{{start_date}} — {{end_date}}</span>
            </div>
            {{#description}}
            <div class="description">{{description}}</div>
            {{/description}}
        </div>
        {{/.}}
    </div>
    {{/experience}}

    {{#education}}
    <div class="section">
        <div class="section-title">Education</div>
        {{#.}}
        <div class="education-item">
            <div class="education-header">
                <div>
                    <span class="degree">{{degree}}</span>
                    <span class="institution">{{institution}}</span>
                </div>
                <span class="year">{{graduation_year}}</span>
            </div>
        </div>
        {{/.}}
    </div>
    {{/education}}

    {{#skills}}
    <div class="section">
        <div class="section-title">Skills</div>
        <div class="skills-grid">
            {{#.}}<span class="skill-tag">{{.}}</span>{{/.}}
        </div>
    </div>
    {{/skills}}
</body>
</html>
        """,
    },
}

def get_template(template_id: str) -> dict:
    """Get template by ID"""
    return TEMPLATES.get(template_id, TEMPLATES["modern"])

def get_all_templates() -> list:
    """Get all available templates"""
    return [
        {
            "id": template_id,
            "name": data["name"],
            "description": data["description"],
            "is_premium": data["is_premium"]
        }
        for template_id, data in TEMPLATES.items()
    ]
