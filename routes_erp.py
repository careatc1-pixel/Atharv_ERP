# routes_erp.py ke add_client function ko replace karein
@erp_bp.route('/add-client', methods=['POST'])
def add_client():
    try:
        # .get() use karne se 'Bad Request' error nahi aayega agar field missing ho
        c = Client(
            company=request.form.get('company'), 
            name=request.form.get('name'), 
            contact=request.form.get('contact'), 
            email=request.form.get('email'), 
            address=request.form.get('address'), 
            gstin=request.form.get('gst')
        )
        db.session.add(c)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"
    
    return redirect(url_for('index'))
