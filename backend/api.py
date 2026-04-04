# This file will contain the backend functionality of an application.
from flask import Flask
import pyrebase
from database import connection
from constant import  properties
from service import validation
import random
from flask import request , jsonify 
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier
from sklearn.metrics import confusion_matrix, accuracy_score , classification_report
from flask import send_file
import io
from flask import render_template
trained_model=None
scaler_model = None
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import matplotlib.pyplot as plt

backend_application = Flask(__name__)
backend_application.config['MAX_CONTENT_LENGTH']=32 * 1024 * 1024
#******************************************************************************************
# Design the feature of an application
#Feature1 - Account creation
@backend_application.route('/createaccount/<userid>/<password>/<confirmpassword>')
def createaccount(userid, password, confirmpassword):
    if not validation.validationid(userid):
        return "Invalid userid - must be at least 6 characters"
    if not validation.validatepassword(password):
        return "Invalid password - must be at least 8 characters"
    if not validation.confirmpassword(password, confirmpassword):
        return "Passwords do not match"
    # Only reaches here if all validation passed
    firebase = pyrebase.initialize_app(connection.databasedetails)
    authobject = firebase.auth()
    try:
        authobject.create_user_with_email_and_password(userid + "@app.in", password)
        return properties.SUCCESS
    except:
        return "User ID already exists"
#*****************************************END************************************************
# Replace the route decorator and function signature with this
@backend_application.route('/personaldetails')
def personaldetails():
    userid    = request.args.get('userid')
    firstname = request.args.get('firstname')
    lastname  = request.args.get('lastname')
    contact   = request.args.get('contact')
    emailid   = request.args.get('emailid')

    if not validation.validatename(firstname):
        return "Invalid first name - no spaces or numbers allowed"
    if not validation.validatename(lastname):
        return "Invalid last name - no spaces or numbers allowed"
    if not validation.validatenumber(contact):
        return "Invalid phone - must be exactly 10 digits"
    if not validation.validateemail(emailid):
        return "Invalid email format"
    if not validation.validationid(userid):
        return "Invalid userid"

    tablename = "personaldetails"
    data = {
        'First_name': firstname,
        'Last_name':  lastname,
        'Contact':    contact,
        'Email_Id':   emailid,
        'User_Id':    userid
    }
    from firebase import firebase
    db = firebase.FirebaseApplication("https://firstapplication-e442f-default-rtdb.firebaseio.com/")
    db.post(tablename, data)
    return properties.SUCCESS
   

#*******************************************************END**************************************************************
# Create an api for login operation
@backend_application.route('/captcha')
def captcha():
    randomnumber=random.randint(1000,9999)
    properties.MACHINECAPTCHA=str(randomnumber)
    return properties.MACHINECAPTCHA
#************************************************************************************************************
@backend_application.route('/login/<userid>/<password>/<captcha>')
def login(userid,password,captcha):
    if not validation.comparecaptcha(captcha, properties.MACHINECAPTCHA):
        return "Wrong captcha"
    
    if (validation.validationid(userid) and validation.validatepassword(password)):
        firebase=pyrebase.initialize_app(connection.databasedetails)
        
        # Check if userid exists in your database first
        databaseobj = firebase.database()
        data = databaseobj.child("personaldetails").get()
        userid_exists = False
        for eachdata in data:
            record = eachdata.val()
            if record and record.get('User_Id') == userid:
                userid_exists = True
                break
        
        if not userid_exists:
            return "Wrong userid"
        
        # Only if userid exists, try password
        authobject = firebase.auth()
        try:
            authobject.sign_in_with_email_and_password(userid + "@app.in", password)
            return properties.SUCCESS
        except Exception as e:
            print("Error", e)
            return "Wrong password"
    
    return properties.FAILED
#************************************************END*******************************************
# Create an API to retrieve personal information based on userid
@backend_application.route('/retrievepd/<userid>')
def retrievepd(userid):
    if(validation.validationid(userid)):
        #Connect to database to retrieve details
        firebase=pyrebase.initialize_app(connection.databasedetails)
        databaseobj=firebase.database()
        data=databaseobj.child("personaldetails").get()
        for eachdata in data:
            record = eachdata.val()
            if record and record.get('User_Id') == userid:
                return record
        return "User Id does not exist"
    return properties.FAILED

#***********************************************END**********************************************
@backend_application.route('/dashboard/<activeuser>')
def dashboard(activeuser):
    firebase=pyrebase.initialize_app(connection.databasedetails)
    databaseobj=firebase.database()
    data=databaseobj.child("personaldetails").get()
    for eachdata in data:
        record = eachdata.val()
        if record and record.get('User_Id') == activeuser:
            fname=eachdata.val()['First_name']
            lname=eachdata.val()['Last_name']
            cname=eachdata.val()['Contact']
            ename=eachdata.val()['Email_Id']
            global uname
            uname=eachdata.val()['User_Id']
            return render_template('dashboard.html',fname=fname,lname=lname,cname=cname,ename=ename,uname=uname)
    return render_template('dashboard.html')
#***************************************************************************************************************
@backend_application.route('/update',methods=['GET','POST'])
def update():
    if request.method=='POST':
        fname=request.form['First_name']
        lname=request.form['Last_name']
        cname=request.form['Contact']
        ename=request.form['Email_Id']
        uname=request.form['User_Id']
        if not validation.validatename(fname):
            return render_template('update.html', message="❌ First name must contain letters only.")
        if not validation.validatename(lname):
            return render_template('update.html', message="❌ Last name must contain letters only.")
        if not validation.validatenumber(cname):
            return render_template('update.html', message="❌ Phone number must be exactly 10 digits.")
        if not validation.validateemail(ename):
            return render_template('update.html', message="❌ Please enter a valid email address.")
        message=modifydetails(fname,lname,cname,ename,uname)
        print(message)
        if (message=='Details Updated successully'):
            return render_template('update.html',message=message)
        else:
            message="Retry again"
            return render_template('update.html',message=message)
    else:
        return render_template('update.html')
#*************************************************************************************************
@backend_application.route('/modifydetails/<First_name>/<Last_name>/<Contact>/<Email_Id>/<User_Id>')
def modifydetails(First_name,Last_name,Contact,Email_Id,User_Id):
    firebase=pyrebase.initialize_app(connection.databasedetails)
    databaseobj=firebase.database()
    data=databaseobj.child("personaldetails").get()
    for eachdata in data:
        record = eachdata.val()
        if record and record.get('User_Id') == User_Id:
            databaseobj.child("personaldetails").child(eachdata.key()).update({'First_name':First_name})
            databaseobj.child("personaldetails").child(eachdata.key()).update({'Last_name':Last_name})
            databaseobj.child("personaldetails").child(eachdata.key()).update({'Contact':Contact})
            databaseobj.child("personaldetails").child(eachdata.key()).update({'Email_Id':Email_Id})
            return "Details Updated successully"
    return "User Id does not exist"
#***************************************************************************************************
@backend_application.route('/deleteaccount/<userid>/<password>')
def deleteaccount(userid, password):
    try:
        firebase = pyrebase.initialize_app(connection.databasedetails)
        authobject = firebase.auth()
        
        #Verify password first by signing in
        try:
            user = authobject.sign_in_with_email_and_password(userid + "@app.in", password)
            print("Token:", user['idToken'])           # ← add this
            authobject.delete_user_account(user['idToken'])
            print("Auth deleted successfully")
        except:
            return "Wrong password"
        
        # Delete from Firebase Auth using the token
        authobject.delete_user_account(user['idToken'])
        
        # Delete from Realtime Database
        databaseobj = firebase.database()
        data = databaseobj.child("personaldetails").get()
        for eachdata in data:
            record = eachdata.val()
            if record and record.get('User_Id') == userid:
                databaseobj.child("personaldetails").child(eachdata.key()).remove()
                break
        
        return properties.SUCCESS
    except Exception as e:
        print("Error deleting account:", e)
        return "Delete failed"

#******************************************************************************************************
@backend_application.route("/ml",methods=['GET','POST'])
def ml():
    if(request.method=='POST'):
        pass
    else:
        return render_template('ml.html',userid=uname)
    return render_template('ml.html',userid=uname)
#*****************************************************************************************************
@backend_application.route("/readxlfile/<path>")
def readxlfile(path):
    try:
        #Read the excel file (dataset1.xlsx)
        df=pd.read_excel(path)
       
            # Remove empty cells
        df=df.dropna()
        # Remove wrong format 
        target_column = df.columns[-1]  
        
        # Separate features and target
        X = df.drop(columns=[target_column])
        y = df[target_column]
        categorical_cols = X.select_dtypes(include=['object', 'string']).columns
        if len(categorical_cols) > 0:
            # Encode categorical variables
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            for col in categorical_cols:
                X[col] = le.fit_transform(X[col].astype(str))
        
        # Convert all numeric columns properly
        numeric_cols = X.select_dtypes(include=['number']).columns
        X[numeric_cols] = X[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # Remove rows with any NaN values after conversion
        X = X.dropna()
        y = y[X.index]  
        
            
        # Remove duplicates
        df=df.drop_duplicates()
        if "patient_id" in X.columns:
            X=X.drop(columns=["patient_id"])
        # Outlier detection using IQR method 
        for col in X.select_dtypes(include=['number']).columns:
            Q1 = X[col].quantile(0.25)
            Q3 = X[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            X = X[(X[col] >= lower_bound) & (X[col] <= upper_bound)]
        
        y = y[X.index]  # Keep corresponding target values after outlier removal
        
        # Combine back for display 
        df_display = pd.concat([X, y], axis=1)
            
        # Get valid dataset
        print(df_display)
        tr= df_display.shape[0]
        tc = X.shape[1]  # Only count feature columns, not target
        colname = X.columns.tolist()  # Only feature column names (excludes target)
        data = df_display.values.tolist()
        filesize=request.content_length or 0
        fs=round(filesize/1024,2)
        return tr,tc,data,colname,fs,X,y
             
         
    except Exception as e:
        print("Error:",e)
        return jsonify({
            "status": "failed",
            "message": str(e)
        })
    
#********************************************END*******************************************************
@backend_application.route("/upload",methods=["POST"])
def upload():
    global trained_model
    file=request.files["myfile"]
    upload_folder=os.path.join(os.getcwd(),"uploads")
    os.makedirs(upload_folder,exist_ok=True)
    filepath=os.path.join(upload_folder,file.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    file.save(filepath)
        
    result = readxlfile(filepath)
    if isinstance(result, tuple) and len(result) == 7:  #  (tr,tc,data,colname,fs,X,y)
        tr, tc, data, colname, fs, X, y = result
    else:
        return "Error processing file", 500  # returns the jsonify error + 500 status

    tr, tc, data, colname, fs, X,y = result
    
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    global scaler_model
    scaler_model = scaler
        
    # Training the model
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.3,random_state=42)

    # XGBoost Model
    model = XGBClassifier(
            n_estimators=600,
            learning_rate=0.03,
            max_depth=6,
            min_child_weight=3,
            subsample=0.85,
            colsample_bytree=0.85,
            gamma=0.2,
            scale_pos_weight=1.5,
            eval_metric='logloss'
        )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    scores=cross_val_score(model, X,y,cv=5)
    print("Average CV:",scores.mean())
    acc = accuracy_score(y_test, y_pred)
    
    print("XBoosting Accuracy:", acc)
    print("Confusion matrix \n",confusion_matrix(y_test,y_pred))
    print("Classification Report:\n",classification_report(y_test,y_pred))
    trained_model=model 
            
        
    firebase = pyrebase.initialize_app(connection.databasedetails)
    databaseobj = firebase.database()
    data_personal = databaseobj.child("personaldetails").get()
    
    fname = lname = cname = ename = ""
    for eachdata in data_personal:
            record = eachdata.val()
            if record and record.get('User_Id') == uname:
                fname = record.get('First_name', '')
                lname = record.get('Last_name', '')
                cname = record.get('Contact', '')
                ename = record.get('Email_Id', '')
                break
    return render_template(
            "dashboard.html",
            rows=tr,
            columns=tc,
            col=colname,
            size=fs,
            fname=fname,
            lname=lname,
            cname=cname,
            ename=ename,
            uname=uname
        )   
#******************************************************************************     
@backend_application.route("/applyml", methods=["POST"])
def applyml():
    global trained_model
    
    if trained_model is None:
        return jsonify({
            "error":"Please upload dataset first"
            })
    
    try:
        age=int(request.form["age"])
        
        #Convert sex and family
        gender=request.form["gender"].lower()
        if gender=="female":
            gender=0
        else:
            gender=1
        family_history=request.form["family_history"] .lower()
        if family_history=="yes":
            family_history=1
        else:
            family_history=0
            
        #SNP values
        snp1=int(request.form["snp1"])
        snp2=int(request.form["snp2"])
        snp3=int(request.form["snp3"])
        snp4=int(request.form["snp4"])
        snp5=int(request.form["snp5"])
        snp6=int(request.form["snp6"])
        snp7=int(request.form["snp7"])
        snp8=int(request.form["snp8"])
        snp9=int(request.form["snp9"])
        snp10=int(request.form["snp10"])
        
        #Gene expression values
        gene1=float(request.form["gene1"])
        gene2=float(request.form["gene2"])
        gene3=float(request.form["gene3"])
        gene4=float(request.form["gene4"])
        gene5=float(request.form["gene5"])
        
        # Create input with proper feature names


        user_data = {
            'age': age,
            'sex': gender,
            'family_history': family_history,
            'snp_1': snp1,
            'snp_2': snp2,
            'snp_3': snp3,
            'snp_4': snp4,
            'snp_5': snp5,
            'snp_6': snp6,
            'snp_7': snp7,
            'snp_8': snp8,
            'snp_9': snp9,
            'snp_10': snp10,
            'gene_expr_1': gene1,
            'gene_expr_2': gene2,
            'gene_expr_3': gene3,
            'gene_expr_4': gene4,
            'gene_expr_5': gene5
            }

        user_input = pd.DataFrame([user_data])

        # Scale the input
        user_input_scaled = scaler_model.transform(user_input)

    # Predict probability
        probability =float( trained_model.predict_proba(user_input_scaled)[0][1] * 100)
        result = round(probability, 2)
        
        print("Probability:",probability)
        print("Returning:",result)
        
        return jsonify({
            "risk_percentage":result
            })
    
    except Exception as e:
        return jsonify({"error": str(e)})
    
#****************************************************************************************
@backend_application.route("/geneticinfo")
def geneticinfo():
    return render_template('geneticinfo.html')
#*****************************************************************************************
@backend_application.route('/download_report/<result>')
def download_report(result):
    result = float(result)
    buffer = io.BytesIO()
    
    NAVY        = colors.HexColor('#0b1f3a')
    TEAL        = colors.HexColor('#0fb8c9')
    OFF_WHITE   = colors.HexColor('#f4f8fb')
    BORDER      = colors.HexColor('#dceaf5')
    MUTED       = colors.HexColor('#5a7085')
    GREEN       = colors.HexColor('#22c55e')
    AMBER       = colors.HexColor('#fbbf24')
    RED         = colors.HexColor('#ef4444')
    WHITE       = colors.white

    #PDF setup 
    pdf = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.6*inch,   bottomMargin=0.6*inch
    )
    elements = []
    styles   = getSampleStyleSheet()
    page_w   = letter[0] - 1.5*inch   # usable width

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=22, leading=28,
        textColor=WHITE,
        fontName='Helvetica-Bold',
        alignment=1,
        spaceAfter=4
    )
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=12, leading=16,
        textColor=NAVY,
        fontName='Helvetica-Bold',
        spaceAfter=8, spaceBefore=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10, leading=15,
        textColor=colors.HexColor('#1a2e44'),
        fontName='Helvetica',
        spaceAfter=4
    )
    muted_style = ParagraphStyle(
        'Muted',
        parent=styles['Normal'],
        fontSize=9, leading=13,
        textColor=MUTED,
        fontName='Helvetica',
        alignment=1
    )
    header_data = [[
        Paragraph("🧬  Genetic Disease Risk Assessment Report", title_style),
    ]]
    header_table = Table(header_data, colWidths=[page_w])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), NAVY),
        ('TOPPADDING',  (0,0), (-1,-1), 22),
        ('BOTTOMPADDING',(0,0),(-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
        ('RIGHTPADDING',(0,0), (-1,-1), 20),
        ('ROUNDEDCORNERS', [6]),
    ]))
    elements.append(header_table)

    # Teal under header
    teal_line = Table([['']], colWidths=[page_w], rowHeights=[3])
    teal_line.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1), TEAL)]))
    elements.append(teal_line)
    elements.append(Spacer(1, 6))

    # Date line
    date_para = Paragraph(
        f"<font color='#5a7085'>Report Generated: </font>"
        f"<font color='#0b1f3a'><b>{datetime.now().strftime('%B %d, %Y  ·  %I:%M %p')}</b></font>",
        ParagraphStyle('date', parent=styles['Normal'], fontSize=9,
                       fontName='Helvetica', spaceAfter=0)
    )
    elements.append(date_para)
    elements.append(Spacer(1, 18))

    #  GAUGE IMAGE  
    fig, ax = plt.subplots(figsize=(6, 2.6))
    fig.patch.set_facecolor('#f4f8fb')
    ax.set_facecolor('#f4f8fb')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)

    # Colour zones
    ax.barh(0.55, 33,   left=0,  height=0.32, color='#22c55e', alpha=0.85)
    ax.barh(0.55, 33,   left=33, height=0.32, color='#fbbf24', alpha=0.85)
    ax.barh(0.55, 34,   left=66, height=0.32, color='#ef4444', alpha=0.85)

    # Zone borders
    for x in [33, 66]:
        ax.axvline(x=x, ymin=0.38, ymax=0.73, color='white', linewidth=1.5)

    # Needle
    ax.plot([result, result], [0.28, 0.82], color='#0b1f3a', linewidth=2.5, solid_capstyle='round')
    ax.plot(result, 0.28, 'o', color='#0b1f3a', markersize=7)

    # Labels
    ax.text(16.5, 0.16, 'LOW RISK',   ha='center', fontsize=9, fontweight='bold', color='#15803d')
    ax.text(49.5, 0.16, 'MEDIUM',     ha='center', fontsize=9, fontweight='bold', color='#a16207')
    ax.text(83,   0.16, 'HIGH RISK',  ha='center', fontsize=9, fontweight='bold', color='#b91c1c')

    # Risk % label above needle
    ax.text(result, 0.88, f'{result:.0f}%',
            ha='center', fontsize=11, fontweight='bold', color='#0b1f3a')

    ax.axis('off')
    plt.tight_layout(pad=0.3)

    gauge_buffer = io.BytesIO()
    plt.savefig(gauge_buffer, format='png', bbox_inches='tight',
                dpi=150, facecolor='#f4f8fb')
    gauge_buffer.seek(0)
    plt.close()

    gauge_img = Image(gauge_buffer, width=5*inch, height=2.2*inch)

    # Wrap gauge in a light card
    gauge_table = Table([[gauge_img]], colWidths=[page_w])
    gauge_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), OFF_WHITE),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',   (0,0), (-1,-1), 14),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('BOX',          (0,0), (-1,-1), 1, BORDER),
        ('ROUNDEDCORNERS', [6]),
    ]))
    elements.append(gauge_table)
    elements.append(Spacer(1, 18))

    #  RESULT TABLE
    # Determine risk level
    if result < 33:
        risk_level   = "LOW RISK"
        risk_color   = GREEN
        risk_bg      = colors.HexColor('#dcfce7')
        interpretation = (
            "Minimal genetic markers detected. Your risk profile is reassuring. "
            "Continue regular health monitoring and maintain a healthy lifestyle."
        )
    elif result < 66:
        risk_level   = "MEDIUM RISK"
        risk_color   = AMBER
        risk_bg      = colors.HexColor('#fef9c3')
        interpretation = (
            "Moderate genetic markers present. Consider genetic counseling and "
            "schedule regular health check-ups to monitor any changes over time."
        )
    else:
        risk_level   = "HIGH RISK"
        risk_color   = RED
        risk_bg      = colors.HexColor('#fee2e2')
        interpretation = (
            "Significant genetic markers detected. Medical consultation is strongly "
            "recommended. Please consult a qualified healthcare provider or genetic "
            "specialist at the earliest opportunity."
        )

    elements.append(Paragraph("Risk Assessment Result", section_heading_style))

    result_data = [
        [
            Paragraph("<font color='#5a7085'>Risk Percentage</font>", muted_style),
            Paragraph("<font color='#5a7085'>Risk Level</font>",       muted_style),
        ],
        [
            Paragraph(f"<b><font color='#0b1f3a' size='18'>{result:.1f}%</font></b>",
                      ParagraphStyle('big', parent=styles['Normal'],
                                     fontSize=18, fontName='Helvetica-Bold', alignment=1)),
            Paragraph(f"<b>{risk_level}</b>",
                      ParagraphStyle('rl', parent=styles['Normal'],
                                     fontSize=14, fontName='Helvetica-Bold',
                                     textColor=risk_color, alignment=1)),
        ]
    ]

    result_table = Table(result_data, colWidths=[page_w/2, page_w/2])
    result_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',    (0,0), (-1,0),  colors.HexColor('#dceaf5')),
        ('TOPPADDING',    (0,0), (-1,0),  8),
        ('BOTTOMPADDING', (0,0), (-1,0),  8),
        # Value row
        ('BACKGROUND',    (0,1), (0,1),   OFF_WHITE),
        ('BACKGROUND',    (1,1), (1,1),   risk_bg),
        ('TOPPADDING',    (0,1), (-1,1),  14),
        ('BOTTOMPADDING', (0,1), (-1,1),  14),
        # Shared
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('BOX',           (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, BORDER),
        ('ROUNDEDCORNERS', [6]),
    ]))
    elements.append(result_table)
    elements.append(Spacer(1, 18))
    
    #  INTERPRETATION CARD
    elements.append(Paragraph("Interpretation & Recommendations", section_heading_style))

    interp_table = Table(
        [[Paragraph(interpretation, body_style)]],
        colWidths=[page_w]
    )
    interp_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), OFF_WHITE),
        ('BOX',           (0,0), (-1,-1), 1, BORDER),
        ('LEFTPADDING',   (0,0), (-1,-1), 16),
        ('RIGHTPADDING',  (0,0), (-1,-1), 16),
        ('TOPPADDING',    (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('ROUNDEDCORNERS', [6]),
    ]))
    elements.append(interp_table)
    elements.append(Spacer(1, 20))

    elements.append(teal_line)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "<b>DISCLAIMER</b>",
        ParagraphStyle('disc_title', parent=styles['Normal'],
                       fontSize=9, fontName='Helvetica-Bold',
                       textColor=MUTED, alignment=1, spaceAfter=3)
    ))
    elements.append(Paragraph(
        "This report is generated based on predictive analysis and should not replace "
        "professional medical advice. Please consult with a qualified healthcare provider "
        "for proper medical evaluation and diagnosis.",
        muted_style
    ))

    #Build & return 
    pdf.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"genetic_risk_report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )
#************************************************************************************************************************************************************************************************
@backend_application.route("/dataset_info")
def dataset_info():
    return render_template("dataset_info.html")
#*********************************************************
@backend_application.route("/download_sample_dataset")
def download_sample_dataset():
    # Path to your sample dataset
    dataset_path = os.path.join(os.getcwd(), "medha_dataset.xlsx")  
    return send_file(
        dataset_path,
        as_attachment=True,
        download_name="sample_genetic_dataset.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
#***********************************************************************************
@backend_application.route('/savehistory/<userid>', methods=['POST'])
def savehistory(userid):
    try:
        data = request.get_json()
        from firebase import firebase
        db = firebase.FirebaseApplication("https://firstapplication-e442f-default-rtdb.firebaseio.com/")
        db.post('predictionhistory', {
            'userid':      userid,
            'name':        data.get('name'),
            'age':         data.get('age'),
            'gender':      data.get('gender'),
            'family_history': data.get('family_history'),
            'risk_percent': data.get('risk_percent'),
            'risk_level':  data.get('risk_level'),
            'date':        datetime.now().strftime('%d %b %Y, %I:%M %p')
        })
        return properties.SUCCESS
    except Exception as e:
        print("Save history error:", e)
        return "Failed"
#**********************************************************************************
@backend_application.route('/gethistory/<userid>')
def gethistory(userid):
    try:
        from firebase import firebase
        db = firebase.FirebaseApplication("https://firstapplication-e442f-default-rtdb.firebaseio.com/")
        data = db.get('predictionhistory', None)
        user_records = []
        if data:
            for key, record in data.items():
                if record.get('userid') == userid:
                    user_records.append(record)
        return jsonify(user_records)
    except Exception as e:
        print("Get history error:", e)
        return jsonify([])
#*******************************************************************************
@backend_application.route('/history/<userid>')
def history(userid):
    try:
        from firebase import firebase
        db = firebase.FirebaseApplication("https://firstapplication-e442f-default-rtdb.firebaseio.com/")
        data = db.get('predictionhistory', None)
        records = []
        if data:
            for key, record in data.items():
                if record.get('userid') == userid:
                    records.append(record)
        # Sort by most recent first
        records.reverse()
        return render_template('history.html', records=records, userid=userid)
    except Exception as e:
        print("History error:", e)
        return render_template('history.html', records=[], userid=userid)
if __name__ == '__main__': 
    backend_application.run(host="0.0.0.0",port=8080)
    
