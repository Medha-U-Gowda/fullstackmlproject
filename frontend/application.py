from tkinter import *
from tkinter import messagebox
import requests
import webbrowser
from properties import constant
from urllib.parse import quote

# Helper: draw a rounded rectangle on a Canvas
def rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    canvas.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=0,   extent=90,  style="pieslice", **kwargs)
    canvas.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90,  style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90,  style="pieslice", **kwargs)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
    canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)

# Styled Entry with teal bottom-border focus
def make_entry(parent, show=None):
    frame = Frame(parent, bg=constant.ENTRY_BG, pady=0)
    e = Entry(
        frame,
        font=constant.FONT_ENTRY,
        bg=constant.ENTRY_BG,
        fg=constant.ENTRY_FG,
        insertbackground=constant.TEAL,
        relief="flat",
        width=constant.ENTRY_WIDTH,
        show=show or ""
    )
    e.pack(side=LEFT, padx=(12, 8), pady=8)
    underline = Frame(frame, bg=constant.TEAL, height=2)
    underline.place(relx=0, rely=1.0, anchor="sw", relwidth=1)
    return frame, e

# Helper: primary teal button
def make_btn_primary(parent, text, command):
    return Button(
        parent, text=text, command=command,
        font=constant.FONT_BTN_PRIMARY,
        bg=constant.BTN_PRIMARY_BG, fg=constant.BTN_PRIMARY_FG,
        activebackground=constant.TEAL_DARK,
        activeforeground=constant.BTN_PRIMARY_FG,
        relief="flat", cursor="hand2",
        padx=20, pady=10, width=20,
        bd=0
    )

# Helper: secondary outline-style button
def make_btn_secondary(parent, text, command):
    return Button(
        parent, text=text, command=command,
        font=constant.FONT_BTN_SECONDARY,
        bg=constant.BTN_SECONDARY_BG, fg=constant.BTN_SECONDARY_FG,
        activebackground=constant.ENTRY_BG,
        activeforeground=constant.TEAL,
        relief="flat", cursor="hand2",
        padx=20, pady=8, width=20,
        bd=0
    )

# Helper: section label
def make_label(parent, text):
    return Label(
        parent, text=text,
        bg=constant.CARD_BG,
        fg=constant.MUTED,
        font=constant.FONT_LABEL,
        anchor="w"
    )

# Helper: card frame
def make_card(parent, width=500, padx=40, pady=30):
    card = Frame(parent, bg=constant.CARD_BG, padx=padx, pady=pady)
    return card

#  BACKEND LOGIC
def loadapplication():
    splash.pack_forget()
    link = "http://127.0.0.1:5000/dashboard/" + activeuser
    webbrowser.open(link)

def retrievepd(userid):
    global activeuser
    activeuser = userid
    url = "http://127.0.0.1:5000/retrievepd/" + userid
    response = requests.get(url)
    print(response.text)
    splash.place(relx=0.5, rely=0.5, anchor="center", width=500, height=300)
    application.after(5000, loadapplication)

def loadcaptcha():
    url = "http://127.0.0.1:5000/captcha"
    response = requests.get(url)
    clabel.configure(text=response.text)

def submit():
    firstname = sfirstnameentry.get()
    lastname  = slastnameentry.get()
    userid    = suseridentry.get()
    email     = semailentry.get()
    passw     = spasswordentry.get()
    cpassw    = scpasswordentry.get()
    phone     = smobileentry.get()

    # ── Validate EVERYTHING before calling any API ──────────
    if not all([firstname, lastname, userid, email, passw, cpassw, phone]):
        messagebox.showwarning(title="Warning", message="Please fill in all fields.")
        return
    if len(userid) < 6:
        messagebox.showwarning(title="Invalid User ID",
                               message="User ID must be at least 6 characters.")
        return
    if len(passw) < 8:
        messagebox.showwarning(title="Weak Password",
                               message="Password must be at least 8 characters.")
        return
    if passw != cpassw:
        messagebox.showwarning(title="Password Mismatch",
                               message="Passwords do not match. Please try again.")
        return
    if not firstname.replace(" ", "").isalpha() or len(firstname.strip()) < 1:
        messagebox.showwarning(title="Invalid First Name",
                               message="First name must contain letters only, no numbers or special characters.")
        return
    if not lastname.replace(" ", "").isalpha() or len(lastname.strip()) < 1:
        messagebox.showwarning(title="Invalid Last Name",
                               message="Last name must contain letters only, no numbers or special characters.")
        return
    if not phone.isdigit() or len(phone) != 10:
        messagebox.showwarning(title="Invalid Phone Number",
                               message="Phone number must be exactly 10 digits.")
        return
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        messagebox.showwarning(title="Invalid Email",
                               message="Please enter a valid email (e.g. name@gmail.com).")
        return

    # ── Only call APIs if ALL validation passed ──────────────
    url = "http://127.0.0.1:5000/createaccount/" + userid + "/" + passw + "/" + cpassw
    response = requests.get(url)
    if response.text == "Operation successful.":
        response2 = requests.get(
            "http://127.0.0.1:5000/personaldetails",
            params={"userid": userid, "firstname": firstname,
                    "lastname": lastname, "contact": phone, "emailid": email}
        )
        if response2.text == "Operation successful.":
            messagebox.showinfo(title="Success", message="Account created successfully!")
            close()
        else:
            messagebox.showwarning(title="Error", message=response2.text)
    else:
        msg = response.text
        if "exists" in msg.lower():
            messagebox.showwarning(title="User ID Taken",
                                   message="This User ID already exists. Please choose a different one.")
        else:
            messagebox.showwarning(title="Error", message=msg)
def close():
    signupframe.place_forget()
    loginframe.place(relx=0, rely=0, relwidth=1, relheight=1)
    luseridentry.focus_set() if luseridentry.get() == "" else lpasswordentry.focus_set()

def createaccount():
    loginframe.place_forget()
    signupframe.place(relx=0, rely=0, relwidth=1, relheight=1)
    sfirstnameentry.focus_set()

def logintoapplication():
    userid   = luseridentry.get()
    password = lpasswordentry.get()
    captcha  = lcaptchaentry.get()
    if not all([userid, password, captcha]):
        messagebox.showwarning(title="Warning", message="Please fill in all fields.")
        return
    try:
        url = "http://127.0.0.1:5000/login/" + userid + "/" + password + "/" + captcha
        response = requests.get(url, timeout=20)
    except requests.exceptions.Timeout:
        messagebox.showwarning(title="Connection Timeout",
                               message="Server took too long. Please try again.")
        return
    except requests.exceptions.ConnectionError:
        messagebox.showwarning(title="Connection Error",
                               message="Could not connect to server. Make sure Flask is running.")
        return
    if response.text == "Operation successful.":
        ok = messagebox.askokcancel(title="Success", message="Logged in successfully. Proceed to dashboard?")
        if ok:
            loginframe.place_forget()
            signupframe.place_forget()
            retrievepd(userid)
    else:
        msg = response.text  # what the server says
        if "captcha" in msg.lower():
            messagebox.showwarning(title="Wrong Captcha",
                                       message="Captcha is incorrect. Click REFRESH and try again.")
        elif "password" in msg.lower():
            messagebox.showwarning(title="Wrong Password",
                                       message="Password is incorrect. Please try again.")
        elif "userid" in msg.lower():
            messagebox.showwarning(title="User Not Found",
                                       message="User ID not found. Please create an account first.")
        else:
            messagebox.showwarning(title="Login Failed",message=f"Error: {msg}")
        loadcaptcha()
#**********************************************************************************************************************
#  APPLICATION WINDOW
application = Tk()
application.state("zoomed")
application.title("GeneticPredict")
application.configure(bg=constant.COMPONENTBGCOLOR)

# Top bar (header)
def make_topbar(parent):
    bar = Frame(parent, bg="#071629", height=56)
    bar.pack(fill=X, side=TOP)
    bar.pack_propagate(False)
    # Logo area
    logo_frame = Frame(bar, bg="#071629")
    logo_frame.pack(side=LEFT, padx=28)
    Label(logo_frame, text="🧬", bg="#071629", font=("Segoe UI", 20)).pack(side=LEFT)
    Label(logo_frame, text="Genetic", bg="#071629", fg="white",
          font=("Segoe UI", 14, "bold")).pack(side=LEFT)
    Label(logo_frame, text="Predict", bg="#071629", fg=constant.TEAL,
          font=("Segoe UI", 14, "bold")).pack(side=LEFT)

#***********************************************************************************************************************
#  LOGIN FRAME
loginframe = Frame(application, bg=constant.COMPONENTBGCOLOR)
loginframe.place(relx=0, rely=0, relwidth=1, relheight=1)

make_topbar(loginframe)

# Centred card
login_card = make_card(loginframe, padx=48, pady=40)
login_card.place(relx=0.5, rely=0.52, anchor="center", width=520)

# Card: Title
Label(login_card, text="Welcome Back 👋",
      bg=constant.CARD_BG, fg="white",
      font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(0, 4))

Label(login_card, text="Sign in to your GeneticPredict account",
      bg=constant.CARD_BG, fg=constant.MUTED,
      font=constant.FONT_MUTED).pack(anchor="w", pady=(0, 28))

# Divider line
Frame(login_card, bg=constant.TEAL, height=2).pack(fill=X, pady=(0, 24))

# User ID
make_label(login_card, "User ID").pack(anchor="w")
l_uid_frame, luseridentry = make_entry(login_card)
l_uid_frame.pack(fill=X, pady=(4, 16))
luseridentry.focus_set()
luseridentry.bind("<Return>", lambda e: lpasswordentry.focus_set())

# Password
make_label(login_card, "Password").pack(anchor="w")
l_pw_frame, lpasswordentry = make_entry(login_card, show="*")
l_pw_frame.pack(fill=X, pady=(4, 16))
lpasswordentry.bind("<Return>", lambda e: lcaptchaentry.focus_set())

# Captcha row
captcha_row = Frame(login_card, bg=constant.CARD_BG)
captcha_row.pack(fill=X, pady=(0, 8))

captcha_left = Frame(captcha_row, bg=constant.CARD_BG)
captcha_left.pack(side=LEFT, fill=X, expand=True)

make_label(captcha_left, "Captcha").pack(anchor="w")
l_cap_frame, lcaptchaentry = make_entry(captcha_left)
l_cap_frame.pack(fill=X, pady=(4, 0))
lcaptchaentry.bind("<Return>", lambda e: logintoapplication())

# Captcha display + refresh
captcha_right = Frame(captcha_row, bg=constant.CARD_BG, padx=14)
captcha_right.pack(side=RIGHT, anchor="s")

clabel = Label(captcha_right, text="ABCD",
               bg="#071629", fg=constant.TEAL,
               font=constant.FONT_CAPTCHA,
               padx=10, pady=6, relief="flat",
               bd=0, width=6)
clabel.pack(pady=(18, 4))

Button(captcha_right, text="↻ Refresh",
       command=loadcaptcha,
       font=("Segoe UI", 9),
       bg=constant.ENTRY_BG, fg=constant.TEAL,
       activebackground=constant.CARD_BG,
       activeforeground=constant.TEAL,
       relief="flat", cursor="hand2", bd=0).pack()

#  Buttons
Frame(login_card, bg=constant.CARD_BG, height=10).pack()  # spacer

make_btn_primary(login_card, "→  Sign In", logintoapplication).pack(fill=X, pady=(4, 10))
make_btn_secondary(login_card, "Create a new account", createaccount).pack(fill=X)

# Bottom hint
Label(login_card, text='Press Enter to move between fields',
      bg=constant.CARD_BG, fg=constant.MUTED,
      font=("Segoe UI", 9)).pack(pady=(16, 0))
#*********************************************************************************************************************
#  SIGNUP FRAME
signupframe = Frame(application, bg=constant.COMPONENTBGCOLOR)
signupframe.place(relx=0, rely=0, relwidth=1, relheight=1)
signupframe.place_forget()

make_topbar(signupframe)

# Scrollable canvas with mousewheel support
signup_canvas = Canvas(signupframe, bg=constant.COMPONENTBGCOLOR,
                       highlightthickness=0)
signup_scrollbar = Scrollbar(signupframe, orient=VERTICAL,
                              command=signup_canvas.yview)
signup_canvas.configure(yscrollcommand=signup_scrollbar.set)

signup_scrollbar.pack(side=RIGHT, fill=Y)
signup_canvas.pack(side=LEFT, fill=BOTH, expand=True)

signup_inner = Frame(signup_canvas, bg=constant.COMPONENTBGCOLOR)
signup_window = signup_canvas.create_window((0, 0), window=signup_inner,
                                             anchor="nw")

def on_signup_resize(event):
    # Keep inner frame as wide as the canvas
    signup_canvas.itemconfig(signup_window, width=event.width)

def on_signup_frame_configure(event):
    # Update scroll region whenever content size changes
    signup_canvas.configure(scrollregion=signup_canvas.bbox("all"))

signup_canvas.bind("<Configure>", on_signup_resize)
signup_inner.bind("<Configure>", on_signup_frame_configure)

# Mousewheel scrolling
def on_mousewheel(event):
    signup_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
signup_canvas.bind_all("<MouseWheel>", on_mousewheel)

# Card inside the scrollable area
signup_card = make_card(signup_inner, padx=48, pady=40)
signup_card.pack(pady=30, padx=40, anchor="center")

# Card: Title
Label(signup_card, text="Create Account 🧬",
      bg=constant.CARD_BG, fg="white",
      font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(0, 4))

Label(signup_card, text="Fill in your details to get started",
      bg=constant.CARD_BG, fg=constant.MUTED,
      font=constant.FONT_MUTED).pack(anchor="w", pady=(0, 24))

Frame(signup_card, bg=constant.TEAL, height=2).pack(fill=X, pady=(0, 20))

# First + Last name
name_row = Frame(signup_card, bg=constant.CARD_BG)
name_row.pack(fill=X, pady=(0, 14))

name_left = Frame(name_row, bg=constant.CARD_BG)
name_left.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
make_label(name_left, "First Name").pack(anchor="w")
sn_left_frame, sfirstnameentry = make_entry(name_left)
sn_left_frame.pack(fill=X, pady=(4, 0))
sfirstnameentry.bind("<Return>", lambda e: slastnameentry.focus_set())

name_right = Frame(name_row, bg=constant.CARD_BG)
name_right.pack(side=RIGHT, fill=X, expand=True, padx=(8, 0))
make_label(name_right, "Last Name").pack(anchor="w")
sn_right_frame, slastnameentry = make_entry(name_right)
sn_right_frame.pack(fill=X, pady=(4, 0))
slastnameentry.bind("<Return>", lambda e: suseridentry.focus_set())

# User ID
make_label(signup_card, "User ID").pack(anchor="w")
s_uid_frame, suseridentry = make_entry(signup_card)
s_uid_frame.pack(fill=X, pady=(4, 14))
suseridentry.bind("<Return>", lambda e: semailentry.focus_set())

# Email
make_label(signup_card, "Email Address").pack(anchor="w")
s_em_frame, semailentry = make_entry(signup_card)
s_em_frame.pack(fill=X, pady=(4, 14))
semailentry.bind("<Return>", lambda e: smobileentry.focus_set())

# Phone
make_label(signup_card, "Phone Number").pack(anchor="w")
s_ph_frame, smobileentry = make_entry(signup_card)
s_ph_frame.pack(fill=X, pady=(4, 14))
smobileentry.bind("<Return>", lambda e: spasswordentry.focus_set())

# Password + Confirm Password
pw_row = Frame(signup_card, bg=constant.CARD_BG)
pw_row.pack(fill=X, pady=(0, 20))

pw_left = Frame(pw_row, bg=constant.CARD_BG)
pw_left.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
make_label(pw_left, "Password").pack(anchor="w")
s_pw_frame, spasswordentry = make_entry(pw_left, show="*")
s_pw_frame.pack(fill=X, pady=(4, 0))
spasswordentry.bind("<Return>", lambda e: scpasswordentry.focus_set())

pw_right = Frame(pw_row, bg=constant.CARD_BG)
pw_right.pack(side=RIGHT, fill=X, expand=True, padx=(8, 0))
make_label(pw_right, "Confirm Password").pack(anchor="w")
s_cpw_frame, scpasswordentry = make_entry(pw_right, show="*")
s_cpw_frame.pack(fill=X, pady=(4, 0))
scpasswordentry.bind("<Return>", lambda e: submit())

# Buttons
make_btn_primary(signup_card, "✓  Create Account", submit).pack(fill=X, pady=(4, 10))
make_btn_secondary(signup_card, "← Back to Login", close).pack(fill=X)

Label(signup_card, text="All fields are required",
      bg=constant.CARD_BG, fg=constant.MUTED,
      font=("Segoe UI", 9)).pack(pady=(14, 0))
#***********************************************************************************************************************
#  SPLASH SCREEN
splash = Frame(application, bg=constant.CARD_BG,
               relief="flat", bd=0)
splash.place(relx=0.5, rely=0.5, anchor="center", width=500, height=260)
splash.place_forget()

Label(splash, text="🧬", bg=constant.CARD_BG,
      font=("Segoe UI", 40)).pack(pady=(40, 8))
Label(splash, text="Loading your dashboard…",
      bg=constant.CARD_BG, fg="white",
      font=("Segoe UI", 14, "bold")).pack()
Label(splash, text="Please wait a moment",
      bg=constant.CARD_BG, fg=constant.MUTED,
      font=("Segoe UI", 10)).pack(pady=(4, 0))

# Animated dots label
dots_label = Label(splash, text="🦠🦠🦠",
                   bg=constant.CARD_BG, fg=constant.TEAL,
                   font=("Segoe UI", 18))
dots_label.pack(pady=(16, 0))

loadcaptcha()
application.mainloop()