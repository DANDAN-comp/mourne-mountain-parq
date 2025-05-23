from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file, make_response
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.pdfbase.pdfmetrics import stringWidth
import pandas as pd





MEDICAL_QUESTIONS = {
    'q1': "1. Has your doctor ever indicated that you have heart trouble or high blood pressure?",
    'q2': "2. Have you ever been diagnosed with any chronic medical condition?",
    'q3': "3. Are you currently taking prescribed medication?",
    'q4': "4. Do you suffer from pains in your heart or chest or have chest pains "
          "brought on by physical activity?",
    'q5': "5. Do you ever lose balance because of dizziness OR"
          " have you lost consciousness in the last 12 months?",
    'q6': "6. Has your doctor advised in the last 12 months that "
          "you should not take part in physical activity?"
}

PHYSICAL_QUESTIONS = {
    'q8': "8. Do you have any bone or joint problems that could be aggravated by this activity?",
    'q9': "9. Have you any current injuries that could impact your activity?",
    'q10': "10. Have you gone through surgery during the last three months?",
    'q11': "11. Do you have diabetes? If yes, are you taking insulin?",
    'q12': "12. Do you have asthma, or exercise-induced asthma?"
           " (If so, are you required to carry an inhaler?)",
    'q13': "13. Have you a fear of heights, or walking close to edges?",
    'q14': "14. Have you ever taken a stroke, or suffer from vertigo or epilepsy?",
    'q15': "15. Do you have any known allergies (medication, food, bee stings, etc.)?",
    'q16': "16. Has your GP prescribed an EPI-Pen auto injector for emergency use?"
}


# Flask and Mail Config
app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'andrewsdaniel413@gmail.com'
app.config['MAIL_PASSWORD'] = 'nkls yhty hvmy ryeh'
app.config['MAIL_DEFAULT_SENDER'] = 'andrewsdaniel413@gmail.com'

# SQLAlchemy Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///participants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
mail = Mail(app)
db = SQLAlchemy(app)

class ParticipantSummary(db.Model):
    __tablename__ = 'participant_summary'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serial_no = db.Column(db.String(50), unique=True, nullable=False)
    participant_name = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    submitted_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


with app.app_context():
    db.create_all()

def format_date(date_str_or_obj):
    if isinstance(date_str_or_obj, str):
        # Try to parse ISO format date string
        try:
            dt = datetime.strptime(date_str_or_obj, "%Y-%m-%d")
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            return date_str_or_obj  # fallback to original if parsing fails
    elif isinstance(date_str_or_obj, datetime):
        return date_str_or_obj.strftime("%d-%m-%Y")
    else:
        return str(date_str_or_obj)

def generate_filled_pdf(participant_name, event_date, answers, extra_info):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    line_height = 18
    y = height - 50

    def write_line(text, max_width=500):
        nonlocal y
        words = text.split()
        line = ''
        for word in words:
            test_line = f"{line} {word}".strip()
            if stringWidth(test_line, "Helvetica", 12) > max_width:
                c.drawString(50, y, line)
                y -= line_height
                if y < 50:
                    c.showPage()
                    y = height - 50
                line = word
            else:
                line = test_line
        if line:
            c.drawString(50, y, line)
            y -= line_height
            if y < 50:
                c.showPage()
                y = height - 50

    # Header
    write_line("PAR-Q Form – Mourne Mountain Adventures")
    write_line(f"Participant Name: {participant_name}")
    write_line(f"Event Date: {format_date(event_date)}")
    write_line(f"Form submitted on: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    write_line("-" * 80)
    write_line("")

    # Step 1: Medical History
    write_line("Step 1: Medical History")
    for i in range(1, 7):
        answer = answers.get(f'q{i}', 'Not Answered')
        question_text = MEDICAL_QUESTIONS.get(f'q{i}', f'Question {i}')
        write_line(f"{question_text} → {answer}")
    write_line("")
    write_line("-" * 80)
    write_line("")

    if any(answers.get(f'q{i}') == 'Yes' for i in range(1, 7)):
        write_line("⚠️ Advisory: Participant is advised to consult a doctor before participating.")
    write_line("")
    write_line("-" * 80)
    write_line("")

    # Step 2: Physical Capability
    write_line("Step 2: Physical Capability")
    for i in range(8, 17):
        answer = answers.get(f'q{i}', 'Not Answered')
        question_text = PHYSICAL_QUESTIONS.get(f'q{i}', f'Question {i}')
        write_line(f"{question_text} → {answer}")
    write_line("")
    write_line("-" * 80)
    write_line("")

    # Step 3: Contact & Declarations
    write_line("Step 3: Contact & Declarations")
    write_line(f"Partcipant's Mobile Number: {extra_info.get('mobile', 'Not provided')}")
    write_line(f"Emergency Contact Name: {extra_info.get('emContact', 'Not provided')}")
    write_line(f"Emergency Contact Phone: {extra_info.get('Phone', 'Not provided')}")
    write_line("")
    write_line("-" * 80)
    write_line("")

    # Declarations
    write_line("Declarations:")
    for i in range(1, 4):
        checked = "✅ Yes" if extra_info.get(f'declaration{i}') else "❌ No"
        write_line(f"Declaration {i}: {checked}")
    write_line("")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer



@app.route('/')
def index():
    return render_template('MM.html')  # Make sure MM.html exists in /templates

@app.route('/dashboard')
def dashboard():
    participants = ParticipantSummary.query.order_by(ParticipantSummary.event_date.asc()).all()
    return render_template('dashboard.html', participants=participants)

@app.route('/delete-selected', methods=['POST'])
def delete_selected():
    try:
        ids = request.form.getlist('delete_ids')
        if ids:
            ParticipantSummary.query.filter(ParticipantSummary.id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        return f"Error deleting records: {e}", 500



@app.route('/submit-parq', methods=['POST'])
def submit_parq():
    data = request.form

    # Extract participant details
    participant_name = data.get('participantName')
    event_date = data.get('eventDate')

    # Extract questions q1–q6 and q8–q16
    answers = {f'q{i}': data.get(f'q{i}') for i in list(range(1, 7)) + list(range(8, 17))}

    # Additional information
    extra_info = {
        'mobile': data.get('mobile'),
        'emContact': data.get('emContact'),
        'Phone': data.get('Phone'),
        'formSubmissionDate': data.get('formSubmissionDate'),
        'declaration1': data.get('declaration1'),
        'declaration2': data.get('declaration2'),
        'declaration3': data.get('declaration3')
    }

    # ✅ Save to database
    try:
        new_participant = ParticipantSummary(
            serial_no=f"{participant_name}_{event_date}_{datetime.now().timestamp()}",
            participant_name=participant_name,
            event_date=datetime.strptime(event_date, "%Y-%m-%d").date(),
            submitted_on=datetime.utcnow()
        )
        db.session.add(new_participant)
        db.session.commit()
    except Exception as db_error:
        db.session.rollback()
        return f"Database error: {str(db_error)}", 500

    # Generate PDF
    pdf_bytes = generate_filled_pdf(participant_name, event_date, answers, extra_info)

    # Email the PDF
    try:
        msg = Message(
            subject=f"New PAR-Q Submission: {participant_name}",
            recipients=['daniel@donite.com'],
            body=f"A new PAR-Q form has been submitted for {participant_name}."
        )

        msg.attach(
            filename=f"{participant_name}-{format_date(event_date)}.pdf",
            content_type="application/pdf",
            data=pdf_bytes.getvalue()
        )

        mail.send(msg)
    except Exception as e:
        return f"Email sending failed: {str(e)}", 500

    # Rewind and return PDF for download
    pdf_bytes.seek(0)
    return send_file(
        pdf_bytes,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{participant_name}_parq.pdf'
    )


@app.route('/download-excel')
def download_excel():
    participants = ParticipantSummary.query.order_by(ParticipantSummary.event_date.asc()).all()

    data = [{
        'Name': p.participant_name,
        'Event Date': p.event_date.strftime('%d-%m-%Y'),
        'Submitted On': p.submitted_on.strftime('%d-%m-%Y')
    } for p in participants]

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Participants')

    output.seek(0)

    return send_file(
        output,
        download_name="participant_data.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route('/clear-db', methods=['POST'])
def clear_db():
    try:
        num_deleted = ParticipantSummary.query.delete()
        db.session.commit()
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        return f"Error clearing database: {e}", 500


# Run App
if __name__ == '__main__':
    app.run(debug=True)
