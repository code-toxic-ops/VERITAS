"""Training-corpus generator for VERITAS.

WHY THIS EXISTS: the model needs labelled examples, and a fresh checkout has no internet
and no licensed dataset. This module composes thousands of varied messages and URLs from
templates so the models can be trained out of the box.

HONEST LIMITATION: synthetic text is cleaner and less diverse than real messages. The
models trained on it are a working foundation, not a finished product. Drop real labelled
data into backend/data/ (see README) and run `python train.py` to improve them. The
hand-written test set in data/holdout.json is NEVER used for training, so the accuracy
reported by train.py is measured on text the generator did not produce.
"""

from __future__ import annotations

import random

R = random.Random(7)


def pick(seq):
    return R.choice(seq)


NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Rohan", "Anjali", "Vikram", "Neha", "Arjun", "Pooja",
         "Karan", "Divya", "Sahil", "Meera", "Ishaan", "Kavya", "Aditya", "Riya", "Manish", "Tanvi"]
COMPANIES = ["Google", "Amazon", "Microsoft", "TCS", "Infosys", "Wipro", "Accenture", "Cognizant",
             "Flipkart", "Deloitte", "IBM", "Capgemini", "HCL", "Adobe", "Zomato", "Swiggy", "Paytm",
             "Reliance Jio", "Tech Mahindra", "Samsung"]
BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Bank", "PNB", "Bank of Baroda", "Canara Bank"]
BANK_DOMAIN = {"SBI": "sbi.co.in", "HDFC Bank": "hdfcbank.com", "ICICI Bank": "icicibank.com",
               "Axis Bank": "axisbank.com", "Kotak Bank": "kotak.com", "PNB": "pnbindia.in",
               "Bank of Baroda": "bankofbaroda.in", "Canara Bank": "canarabank.com"}
WALLETS = ["Paytm", "PhonePe", "Google Pay", "BHIM"]
MERCHANTS = ["Amazon", "Flipkart", "Myntra", "Zomato", "Swiggy", "Big Bazaar", "Reliance Smart", "Croma",
             "BookMyShow", "Uber", "Ola", "DMart", "Nykaa", "Ajio"]
ROLES = ["internship", "work from home job", "data entry role", "software trainee position", "HR executive role",
         "customer support job", "content writer position", "online typing job", "digital marketing internship"]
FEES = ["registration fee", "refundable security deposit", "training kit charges", "processing fee",
        "verification charges", "joining fee", "ID card charges", "background check fee"]
PORTALS = ["Naukri", "LinkedIn", "Internshala", "Indeed", "Shine"]
SCAM_TLD = ["xyz", "top", "click", "live", "site", "online", "icu", "buzz", "cfd", "sbs", "vip", "link",
            "work", "support", "tk", "ml", "ga", "cf"]
EMOJI = ["🎉", "✅", "⚠️", "🔥", "💰", "📢", "👉", "🎁", "😊", "🙏", "📱", "✨"]
SCAM_KW = ["login", "verify", "secure", "update", "kyc", "claim", "reward", "refund", "gift", "unlock",
           "support", "apply", "register", "winner", "account", "confirm", "bonus", "pay"]


def _slug(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _phone() -> str:
    return pick(["+91 ", "", "+91-", "0"]) + str(R.randint(6, 9)) + "".join(str(R.randint(0, 9)) for _ in range(9))


def _scam_link(co: str, bank: str) -> str:
    brand = _slug(pick([co, bank.split()[0], co]))
    kw = pick(SCAM_KW)
    tld = pick(SCAM_TLD)
    kind = R.random()
    scheme = pick(["http://", "https://", "https://", "http://", ""])
    if kind < 0.40:
        host = pick([f"{brand}-{kw}.{tld}", f"{kw}-{brand}.{tld}", f"{brand}{kw}.{tld}", f"{brand}-{kw}-{pick(SCAM_KW)}.{tld}"])
    elif kind < 0.55:
        host = f"{brand.replace('o', '0').replace('l', '1', 1)}-{kw}.{pick(['com', 'in', 'net', tld])}"
    elif kind < 0.67:
        host = f"{brand}.com.{kw}-{pick(SCAM_KW)}.{tld}"
    elif kind < 0.77:
        host = f"{pick(['bit.ly', 'tinyurl.com', 'cutt.ly', 'rb.gy', 't.co'])}/{_rand_code(R.randint(5, 8))}"
    elif kind < 0.85:
        host = f"{R.randint(11, 223)}.{R.randint(0, 255)}.{R.randint(0, 255)}.{R.randint(1, 254)}"
        return f"http://{host}{pick(['/login', '/verify.php', ':8080/pay', '/kyc', '/'])}"
    elif kind < 0.93:
        host = f"{brand}-{kw}.{pick(['weebly.com', 'netlify.app', 'web.app', '000webhostapp.com', 'blogspot.com', 'pages.dev'])}"
    else:
        host = f"{_rand_code(R.randint(7, 11))}.{tld}"
    path = pick(["", "/", f"/{kw}", f"/{kw}/{_rand_code(5)}", "/apply", "/login.php", f"/{kw}?id={R.randint(100, 99999)}"])
    return f"{scheme}{host}{path}"


def _spam_link(co: str) -> str:
    b = _slug(co)
    return pick([
        f"https://www.{b}.com/offers", f"https://{b}.in/sale?utm_source=sms", f"https://bit.ly/{_rand_code(6)}",
        f"https://shop.{b}.com/deals", f"www.{b}.com/shop", f"https://www.{b}.com/webinar/register",
        f"https://m.{b}.in/app", f"https://{b}.com/unsubscribe", f"https://tinyurl.com/{_rand_code(6)}",
    ])


def _good_link(co: str, bank: str) -> str:
    b = _slug(co)
    return pick([
        f"https://www.{b}.com/track", f"https://careers.{b}.com/jobs", f"https://www.{BANK_DOMAIN[bank]}/help",
        f"https://{b}.com/orders", f"https://www.{b}.com/support", f"https://netbanking.{BANK_DOMAIN[bank]}",
        "https://www.irctc.co.in", "https://scholarships.gov.in", "https://www.uidai.gov.in",
    ])


def _rand_code(n: int) -> str:
    return "".join(R.choice("abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(n))


def _ctx(kind: str) -> dict:
    co, bank = pick(COMPANIES), pick(BANKS)
    link = {"scam": _scam_link, "spam": lambda c, b: _spam_link(c), "genuine": _good_link}[kind](co, bank)
    return dict(
        co=co, bank=bank, wallet=pick(WALLETS), name=pick(NAMES), merchant=pick(MERCHANTS),
        amt=pick(["₹199", "₹299", "₹499", "₹999", "Rs 1,200", "Rs. 1500", "₹2,000", "₹2500", "INR 750", "₹3,499", "Rs 5000", "Rs.350"]),
        amt2=pick(["₹1,250", "Rs 640", "₹3,200", "Rs. 899", "INR 2,100", "₹15,000", "Rs 45,000", "₹780.50"]),
        big=pick(["₹25,000", "Rs 50,000", "₹1,00,000", "₹5 lakh", "Rs 10,00,000", "₹2,50,000", "$5000", "₹75,000", "Rs 25 lakh"]),
        code=str(R.randint(1000, 999999)), phone=_phone(), hrs=pick(["2", "3", "6", "12", "24", "48"]),
        mins=pick(["2", "3", "5", "10", "15"]), url=link, date=pick(["12 March", "5th April", "Monday", "tomorrow", "30 June", "15th", "Friday", "this Sunday"]),
        tg="@" + pick(["hr_" + _slug(pick(COMPANIES)), "earnwithus", "jobs_official", "tradepro", "kbc_claims", "support_desk"]),
        role=pick(ROLES), fee=pick(FEES), portal=pick(PORTALS), when=pick(["today", "now", "within 2 hours", "immediately", "before 6 PM"]),
        acct=str(R.randint(1000, 9999)), ref=str(R.randint(10000, 99999999)), pnr=str(R.randint(1000000000, 9999999999)),
        time=pick(["10:30 AM", "11 AM", "2 PM", "4:15 PM", "9 AM", "5 PM", "6:30 PM"]), city=pick(["Noida", "Pune", "Bengaluru", "Delhi", "Hyderabad", "Chennai"]),
        exam=pick(["mid-semester", "end-semester", "viva", "internal assessment", "lab practical"]), dr=pick(["Sharma", "Gupta", "Reddy", "Khan", "Iyer"]),
        pct=pick(["30", "40", "50", "60", "70", "80"]), item=pick(["order", "parcel", "package", "shipment"]),
        app=pick(["Instagram", "Amazon", "Google", "WhatsApp", "Swiggy", "Paytm", "Microsoft"]), svc=pick(["Netflix", "Spotify", "Hotstar", "Prime", "YouTube Premium"]),
    )


def _build(parts: list, ctx: dict) -> str:
    out = []
    for p in parts:
        if isinstance(p, tuple):
            prob, opts = p
            if R.random() > prob:
                continue
            p = opts
        out.append(R.choice(p) if isinstance(p, list) else p)
    return " ".join(out).format(**ctx)


# --------------------------------------------------------------------------------------
# SCAM: every skeleton is a list of parts; a list picks one option, (prob, list) is optional.
# --------------------------------------------------------------------------------------
SCAM = [
    # fake job / internship fee
    [["Congratulations! You have been selected for the {role} at {co}.", "Dear candidate, your resume is shortlisted by {co} for a {role}. No interview is required.",
      "{co} HR Team: you are selected for {role}. Offer letter will be issued today.", "Hello, this is HR from {co}. We found your profile on {portal} and you are selected for a {role}."],
     ["Pay {amt} as {fee} to confirm your seat.", "Deposit {amt} towards {fee} and your joining letter will be released.", "To secure your position transfer {amt} ({fee}) {when}.", "A {fee} of {amt} is mandatory, it is fully refundable after joining."],
     (.85, ["Contact HR on WhatsApp {phone}.", "Message us on Telegram {tg} for the payment details.", "Register here: {url}", "Click {url} to complete registration.", "Send your Aadhaar and PAN card photo to complete verification."]),
     (.5, ["Limited seats, hurry!", "Offer valid only for {hrs} hours.", "Reply within {hrs} hours or your selection will be cancelled.", "Last chance, confirm today."])],
    # bank KYC / block + otp
    [["Dear customer, your {bank} account will be blocked within {hrs} hours as your KYC is pending.", "{bank} ALERT: Your account has been suspended due to incomplete KYC.", "Your {bank} net banking is deactivated. KYC update is mandatory.", "Dear {bank} user, your debit card is blocked. Update PAN details to reactivate."],
     ["Update immediately at {url}", "Click {url} to verify your identity.", "Login to {url} and complete the verification.", "Call {phone} now to avoid closure."],
     (.7, ["Share the OTP you receive to verify.", "Enter your card number, CVV and OTP to confirm.", "Send your PIN and OTP to the executive.", "Provide your net banking password to activate."]),
     (.4, ["Failure to do so will lead to permanent closure.", "Act now to avoid penalty.", "This is your final notice."])],
    # task / work from home earning
    [["Work from home and earn {big} per month. No experience needed.", "Earn {amt} daily by liking videos and rating products. Only 2 hours of work.", "Part time job offer: complete simple online tasks and get paid {amt} per task.",
      "Hiring for online task jobs, salary {big}, no interview required."],
     ["Join our Telegram channel {tg} to start.", "Message us on WhatsApp {phone} now.", "Add this number on WhatsApp for the task link {phone}."],
     (.6, ["First pay {amt} as a deposit and you will get it back with commission.", "A small refundable deposit of {amt} is required to activate your account.", "Recharge {amt} to unlock higher level tasks."]),
     (.5, ["Only {mins} slots left!", "Do not share this with anyone.", "Hurry, limited positions."])],
    # lottery / prize
    [["Congratulations! You have won {big} in the {co} lucky draw.", "You are the lucky winner of {big} in the KBC lottery!", "Your mobile number has won {big} in the {co} anniversary lucky draw.", "Winner! You have been selected for a free iPhone from {co}."],
     ["To claim your prize, pay {amt} as processing charges.", "Send {amt} as tax to release the amount to your account.", "Contact our agent on WhatsApp {phone} with your bank details to claim.", "Click {url} to claim your reward now."],
     (.5, ["Offer expires in {hrs} hours.", "Do not tell anyone until you receive the prize.", "Claim within {hrs} hours or the prize will be given to someone else."])],
    # scholarship / government scheme
    [["Your National Scholarship application is approved for {big}.", "Dear student, your scholarship of {amt} is sanctioned by the government.", "PM Yojana: you are eligible for a cash benefit of {big}.", "Your scholarship amount is ready for transfer."],
     ["Transfer {amt} as a processing fee to release the amount.", "Send your bank account number, PIN and OTP to claim.", "Apply now at {url}", "Pay {amt} for verification and get the funds today."],
     (.6, ["Reply within {hrs} hours or your application will be cancelled.", "Last date is today!", "Do not share this message."])],
    # courier / customs
    [["Your {item} is held at customs.", "We tried to deliver your {item} but the address was incomplete.", "{co} Courier: your {item} could not be delivered.", "Your international {item} is on hold."],
     ["Pay a clearance fee of {amt} to release it.", "Confirm your address and pay {amt} re-delivery charge at {url}", "Pay {amt} customs duty now: {url}", "Update your details at {url} within {hrs} hours or it will be returned."],
     (.4, ["Failure to pay will result in legal action.", "Final reminder."])],
    # electricity disconnect
    [["Dear consumer, your electricity connection will be disconnected tonight at 9:30 PM because your previous month bill is not updated.", "URGENT: Power supply will be cut today. Last bill not paid.",
      "Your electricity bill is overdue and the connection will be terminated in {hrs} hours."],
     ["Call the electricity officer immediately on {phone}.", "Contact {phone} to update your bill now.", "Pay now at {url} to avoid disconnection.", "Message {phone} on WhatsApp right away."]],
    # investment / crypto / trading
    [["Invest {amt} today and get {big} in 7 days. Guaranteed returns!", "Double your money in 30 days with our expert trading tips. 100% profit guaranteed.", "Join our VIP stock tips group. Daily profit {big}, risk free.", "Bitcoin investment opportunity: earn 20% daily returns."],
     ["Join Telegram {tg} now.", "Register at {url} and deposit {amt} to start.", "WhatsApp {phone} for the investment plan.", "Limited slots, deposit {amt} today."],
     (.4, ["Hurry, offer ends tonight.", "Don't miss this once in a lifetime chance."])],
    # loan with fee
    [["Instant loan approved up to {big} without documents or CIBIL check.", "Your pre-approved personal loan of {big} is ready. No credit score needed.", "Get {big} loan in 10 minutes, 100% approval guaranteed."],
     ["Pay {amt} as insurance fee to release the amount.", "Transfer {amt} processing charges to get the loan today.", "Click {url} and pay {amt} to activate.", "WhatsApp {phone} to proceed."],
     (.4, ["Offer valid today only.", "Reply now."])],
    # family / boss impersonation
    [["Hi, this is {name}. I lost my phone, this is my new number.", "Hello mom, it's {name}, my phone broke so I'm using a friend's number.", "Hi, are you available? I need a quick favour, I am in a meeting.", "This is your manager. I need you to handle something confidential."],
     ["Can you transfer {amt2} urgently? I will pay you back tonight.", "Please buy gift cards worth {amt2} and send me the codes, it's urgent.", "Send {amt2} to this UPI id right away, my card is not working.", "Pay this bill of {amt2} for me, I will explain later."],
     (.6, ["Please don't call, just send it.", "Don't tell anyone about this.", "Reply as soon as you see this."])],
    # digital arrest / police / TRAI
    [["This is {city} Cyber Police. A parcel in your name contains illegal items.", "TRAI notice: your SIM will be disconnected due to illegal activity.", "CBI officer here. Your Aadhaar is linked to a money laundering case.", "This is a final legal notice: an FIR is registered against your number."],
     ["You are under digital arrest. Do not disconnect the call.", "Pay {big} as a security deposit to close the case, otherwise you will be arrested.", "Do not tell anyone, stay on the video call until we verify.", "Transfer {amt2} to the RBI safe account for verification."],
     (.5, ["Call {phone} immediately.", "Failure to cooperate will lead to arrest within {hrs} hours."])],
    # refund / UPI collect
    [["Your refund of {amt2} is pending.", "You have received a cashback of {amt2} from {wallet}.", "Congratulations, {amt2} has been credited as a reward.", "A payment of {amt2} is waiting for you."],
     ["Enter your UPI PIN to receive the money.", "Scan this QR code and enter your PIN to accept.", "Approve the collect request to get the amount.", "Click {url} and enter your card details to claim it.", "Share the OTP to receive the refund."],
     (.4, ["Expires in {mins} minutes.", "Claim now."])],
    # account compromised / subscription / password phishing
    [["Your {svc} payment failed. Update your billing details within {hrs} hours or your account will be cancelled.", "Security alert: unusual sign in to your {app} account. Verify now.",
      "Your {co} account has been locked due to suspicious activity.", "Your mailbox storage is full. Verify your password to avoid losing emails.", "Your {co} order of {amt2} was placed. If this wasn't you, cancel it at the link."],
     ["Verify here: {url}", "Click {url} and enter your password to restore access.", "Confirm your login details at {url}", "Sign in at {url} to keep your account active."],
     (.4, ["Failure to respond will result in permanent suspension.", "Act within {hrs} hours."])],
    # tax refund / aadhaar / pan
    [["Income Tax Department: you are eligible for a refund of {amt2}.", "Your PAN card will be deactivated if not linked with Aadhaar today.", "Your Aadhaar has been suspended due to a verification issue.", "Dear taxpayer, a tax refund is approved for your account."],
     ["Submit your bank details and card number at {url} to receive the amount.", "Share the OTP received on your phone to reactivate immediately.", "Update PAN at {url} now.", "Call {phone} to complete the process."],
     (.4, ["Last date is today.", "Do not delay."])],
    # tech support
    [["Microsoft Security Alert: your computer is infected with a virus.", "Your antivirus subscription of {amt2} has been auto renewed.", "WARNING: your device has been hacked.", "{co} support: suspicious activity detected on your device."],
     ["Call toll free {phone} now. Do not restart your PC.", "Call {phone} to cancel the charge immediately.", "Install this app from {url} so our technician can fix it.", "Contact support at {phone} before your data is lost."]],
    # advance fee / 419
    [["Dear friend, I am Mr {name}, a banker. I have {big} in an unclaimed account to transfer.", "I am a soldier posted abroad and I have funds worth {big} that I need to move safely.", "You have been chosen to receive a donation of {big} from a charity foundation."],
     ["I need your bank account details to transfer the funds.", "You will receive 30 percent for your help. Reply urgently.", "Send {amt} for the legal documents and the money will be released.", "Keep this strictly confidential."]],
    # Hindi / Hinglish
    [["आपका KYC अपडेट नहीं है। आपका बैंक खाता बंद कर दिया जाएगा।", "बधाई हो! आपने {big} की लॉटरी जीती है।", "आपका आधार कार्ड निलंबित कर दिया गया है।", "आपकी नौकरी {co} में पक्की हो गई है।"],
     ["तुरंत ओटीपी शेयर करें।", "अभी इस लिंक पर क्लिक करें {url}", "रजिस्ट्रेशन फीस {amt} जमा करें।", "{phone} पर WhatsApp करें, किसी को न बताएं।"]],
    [["Aapka {bank} account block ho jayega, abhi KYC update karein.", "Aapko {co} se {big} ka gift voucher mila hai!", "Congratulations, aapne lucky draw jeeta hai.", "Aapki {co} me job confirm ho gayi hai."],
     ["Claim karne ke liye link par click karo {url}", "Abhi OTP bhejiye warna account band ho jayega.", "{amt} registration fee jama karein.", "{phone} par WhatsApp karo, kisi ko mat batana."]],
]

# --------------------------------------------------------------------------------------
# SPAM: unsolicited promotion. Annoying, but not trying to steal credentials or money-first.
# --------------------------------------------------------------------------------------
SPAM = [
    [["FLAT {pct}% OFF on all fashion at {co}!", "Mega Sale at {merchant}: up to {pct}% off on electronics.", "Big Billion Days start tonight! Up to {pct}% off on mobiles and laptops.", "Festive offer: Buy 1 Get 1 free at {merchant}.", "End of season clearance, flat {pct}% off sitewide."],
     ["Shop now at {url}", "Order now on the app.", "Visit your nearest store this week.", "Use code SAVE{pct} at checkout."],
     (.8, ["T&C apply. Reply STOP to opt out.", "To unsubscribe reply STOP.", "Offer valid till {date}.", "Terms and conditions apply."])],
    [["Recharge with {amt} and enjoy unlimited calls with 1.5GB data per day for 28 days.", "Get 2GB per day for just {amt}. Recharge now on the app.", "Upgrade to 5G with {co} and get free Netflix for 3 months.", "New plan alert: {amt} for 84 days validity."],
     ["Visit {url} to recharge.", "Dial *121# to activate.", "Offer valid till {date}."],
     (.7, ["T&C apply.", "Reply STOP to unsubscribe."])],
    [["You are pre-approved for a credit card with lifetime free offer.", "Pre-approved personal loan up to {big} at attractive interest rates from {bank}.", "Apply for the {bank} Platinum card today and earn reward points.", "Low interest home loan starting at 8.5 percent."],
     ["Apply in 2 minutes at {url}", "Call 1800-{code} for details.", "Visit your nearest branch."],
     ["T&C apply. To stop SMS reply STOP.", "Terms and conditions apply. Loan subject to credit approval.", "Subject to bank approval."]],
    [["Learn Digital Marketing from industry experts.", "Join our Python and Data Science bootcamp starting {date}.", "Crack JEE and NEET with our online coaching.", "Master Excel and Power BI in 30 days."],
     ["Enroll now and get {pct}% early bird discount.", "Book a free demo class at {url}", "Call 1800-{code} for a free counselling session."],
     (.7, ["Limited batch size.", "Seats are filling fast.", "Unsubscribe anytime."])],
    [["Download the {merchant} app and get {amt} cashback on your first order.", "Refer a friend and earn {amt} in your wallet.", "Your cart misses you! Items in your cart are selling out fast.", "Order dinner tonight and get free delivery."],
     ["Use code WELCOME{pct}.", "Complete your purchase and get free shipping.", "Install now: {url}"],
     (.6, ["T&C apply.", "Offer ends {date}."])],
    [["Join our free webinar on Cloud Computing this {date}.", "Invitation: AI and Machine Learning summit in {city}.", "Study abroad fair this Sunday. Meet university representatives.", "Don't miss our startup networking event in {city}."],
     ["Register today at {url}", "Free entry for early registrations.", "Seats are limited."],
     (.8, ["Unsubscribe anytime.", "You are receiving this because you subscribed to our newsletter."])],
    [["Get a 1 crore term insurance cover starting at just {amt} per month.", "Secure your family with a life insurance plan from {co}.", "New launch! 2BHK apartments in {city} starting 45 lakh.", "Book a site visit this weekend for our premium villas in {city}."],
     ["Call {phone} for a free quote.", "Compare plans and save tax.", "Visit {url} for details."],
     (.6, ["T&C apply.", "Insurance is the subject matter of solicitation."])],
    [["Happy Diwali from {merchant}! Enjoy up to {pct}% off storewide.", "Happy New Year! Celebrate with {pct}% off at {co}.", "Weekend special: free dessert on every large order.", "Holi Dhamaka sale is live."],
     ["Shop at {url}", "Visit our store this week.", "Order now!"],
     (.6, ["T&C apply.", "Reply STOP to opt out."])],
    [["Win big with fantasy cricket! Deposit and get 200% bonus on your first match.", "Join the casino and get 100% welcome bonus.", "Play rummy online and win cash daily.", "Get 5000 Instagram followers just {amt}. Fast delivery."],
     ["Play now at {url}", "Sign up today.", "DM now for the price list."],
     (.5, ["T&C apply.", "18+ only."])],
    [["Rate your recent experience with {merchant} and help us improve.", "We value your feedback. Take a 2 minute survey about your last visit.", "How was your order? Leave a review for {merchant}."],
     ["Tell us at {url}", "Reply with a rating from 1 to 5."],
     (.5, ["Reply STOP to unsubscribe.", "Thank you for shopping with us."])],
    [["{co} में बंपर सेल! {pct}% तक की छूट।", "{merchant} पर दिवाली ऑफर, अभी खरीदें।", "नया प्लान: सिर्फ {amt} में अनलिमिटेड कॉल।"],
     ["अभी ऑर्डर करें {url}", "ऑफर {date} तक वैध है।", "T&C लागू।"]],
    [["Dhamaka offer! {merchant} par {pct}% tak ki chhoot.", "Naya recharge plan {amt} mein, unlimited calls.", "Apni dream car abhi book karein, special festive offer."],
     ["Abhi shop karein {url}", "Offer {date} tak valid hai.", "T&C apply."]],
]

# --------------------------------------------------------------------------------------
# GENUINE: ordinary legitimate messages, including hard cases that look scary on the surface.
# --------------------------------------------------------------------------------------
GENUINE = [
    # bank OTP with the standard warning
    [["{code} is your OTP for the transaction of {amt2} at {merchant}.", "Your OTP for login to {app} is {code}.", "Use {code} as your verification code for {app}.", "OTP {code} for your {bank} net banking login.", "{code} is the OTP for your payment of {amt2} on {merchant}."],
     ["It is valid for {mins} minutes.", "Valid for {mins} minutes only."],
     ["Never share this OTP with anyone, including bank staff.", "Do not share it with anyone.", "Don't share this code with anyone. {bank} never asks for your OTP.", "Please do not disclose it to anyone."]],
    # debit / credit alert
    [["{amt2} debited from your {bank} A/c XX{acct} on {date}.", "{amt2} credited to your A/c XX{acct} on {date}.", "{amt2} spent on your {bank} credit card XX{acct} at {merchant}.", "UPI payment of {amt2} to {merchant} successful from A/c XX{acct}."],
     ["Ref no {ref}.", "Available balance {amt2}.", "Txn ID {ref}."],
     (.8, ["If not you, call the number printed on the back of your card.", "If this was not you, contact {bank} through the official app or branch.", "Not you? Call {bank} on the official helpline number."])],
    # shipping / delivery
    [["Your {merchant} order #{ref} has been shipped and will arrive by {date}.", "Your {item} from {merchant} was delivered today. Rate your experience in the app.", "Your order is out for delivery and will reach you by {time}.", "{merchant}: your return request #{ref} has been approved. Refund will be processed in 5 to 7 days."],
     (.6, ["Track it in the {merchant} app.", "Track your order on the official website.", "Thanks for shopping with us."]),
     (.3, ["Share OTP {code} with the delivery partner only when you receive the package.", "Delivery OTP is {code}. Give it to the agent only at the time of delivery."])],
    # college / school notice
    [["The {exam} timetable has been published on the college notice board and the student portal.", "Dear students, the {exam} exam will begin at {time} on {date}. Please reach 15 minutes early.", "Tomorrow's lecture is cancelled. Check the portal for the revised schedule.", "Assignment submission deadline is {date}. Late submissions will not be accepted.", "The lab session on Thursday is rescheduled to {time}."],
     (.7, ["Please check your batch schedule.", "Contact the exam cell if you see any clash.", "Carry your ID card.", "Details are on the official student portal."])],
    # college fee through official portal (hard negative: a legit fee)
    [["Dear students, the semester fee of {big} is due by {date}.", "Reminder: tuition fee for the next semester is due on {date}.", "Hostel fee for the coming term is payable by {date}."],
     ["Please pay through the official ERP portal or the college accounts office only.", "Pay at the accounts counter or via the college portal and collect the receipt.", "Payment can be made online on the official university website."],
     (.5, ["Contact the accounts department for any queries.", "A late fine applies after the due date."])],
    # recruiter genuine
    [["Thank you for applying to the {role} at {co}. We have received your application.", "Hi {name}, your interview with the {co} recruitment team is scheduled for {date} at {time}.", "Your application for {role} at {co} is under review.", "We would like to invite you for a technical round on {date}."],
     ["Our team will contact you if you are shortlisted.", "Please join using the link sent from our official careers email.", "Please keep your ID proof ready.", "You can track your status on our careers page {url}"],
     (.7, ["We will never ask you for payment during the hiring process.", "Reply to confirm your slot.", "All the best!"])],
    # friend / family chat
    [["hey are we still meeting at {time}?", "bro send me the notes pls", "reached home, thanks for dinner!", "Happy birthday {name}! Have a great day and a great year ahead.", "Don't forget to buy milk on your way home.", "call me when you are free", "did you watch the match yesterday? it was amazing", "mom says dinner is ready, come home soon", "I'll save you a seat in the library tomorrow.",
      "Congratulations on your promotion! So proud of you.", "lets go for a movie this weekend?", "Thanks for helping me with the project, really appreciate it.", "Are you coming to {city} for the wedding?", "I'm running 10 minutes late, sorry!"]],
    # Hinglish / Hindi casual and notices
    [["bhai kal ka match dekha? mast tha", "Mummy ne bola dinner pe aa jao", "Kal ki class cancel hai, notice portal pe daal diya hai.", "Aaj shaam ko milte hain, {time} baje.", "कल की कक्षा रद्द है, कृपया पोर्टल देखें।", "आपकी परीक्षा कल सुबह 10 बजे शुरू होगी, कृपया समय पर पहुंचें।", "आपका OTP {code} है। इसे किसी से साझा न करें।", "आपका ऑर्डर कल तक पहुंच जाएगा।"]],
    # work chat
    [["Standup is moved to 11:30 today. Please update the sprint board before then.", "PR #{acct} is ready for review when you get a chance.", "Meeting notes are on the shared drive. Let me know if I missed anything.", "The client call is rescheduled to {time} on {date}. Same Teams link.", "Could you send the report by end of day tomorrow? Thanks.", "The build is green now, deploying after lunch.", "Reminder: submit your timesheet by Friday."]],
    # bills / statements
    [["Your electricity bill of {amt2} is generated for this month. Due date {date}.", "Your mobile bill of {amt2} is ready. Pay before {date}.", "Your credit card statement for this month is ready. Total due {amt2}.", "Your broadband bill is generated. Amount due {amt2}."],
     ["Pay through the official app or website.", "View it in the app. You can pay using auto pay.", "Thank you for being a valued customer."]],
    # travel
    [["PNR {pnr}: Your train departs at {time} from {city} platform {acct}.", "Your flight booking is confirmed. Web check in opens 48 hours before departure.", "Your cab will arrive in {mins} minutes. Driver OTP is {code}.", "Your hotel booking in {city} is confirmed for {date}."]],
    # appointments
    [["Reminder: your appointment with Dr {dr} is on {date} at {time}.", "Your dental check up is tomorrow at {time}. Reply to reschedule.", "Your lab test report is ready. You can collect it from the clinic.", "Your vaccination slot is booked for {date} at {time}."]],
    # genuine KYC renewal (hard negative)
    [["Your KYC is due for periodic renewal.", "{bank}: Please update your KYC documents at your home branch.", "Dear customer, complete your re-KYC for your {bank} account."],
     ["Visit your nearest branch with ID and address proof or use the official mobile app.", "You can also update it on our official website."],
     ["We never ask for OTP, PIN or password. Do not share them with anyone.", "{bank} will never call you to ask for your OTP."]],
    # subscription / receipts
    [["Payment of {amt} received for your {svc} subscription. Thank you.", "Your {svc} plan renews on {date}. You can manage it in your account settings.", "Thanks for your purchase! Your invoice is available in your account.", "Your payment of {amt2} to {merchant} was successful."]],
    # govt portal acknowledgements
    [["Your application ref no {ref} has been received.", "Your passport application is submitted successfully. Reference {ref}.", "Your scholarship application has been submitted. Track the status on the official portal.", "Your income tax return has been processed. Details are on the official e-filing portal."],
     (.6, ["No payment is required at this stage.", "You will be informed by email.", "Check the official website for updates."])],
    # legit urgency / deadlines
    [["Last date to submit your exam form is {date}. Please submit it today through the student portal.", "Please confirm your attendance by tonight, we need the headcount for dinner.", "Urgent: the server maintenance starts at {time}, please save your work.", "Hurry up, the bus leaves in 10 minutes!", "Please reply by {date} so we can finalise the seating."]],
]


def _noise(s: str, kind: str, ctx: dict) -> str:
    if R.random() < 0.16:
        s = s.lower()
    elif R.random() < 0.05:
        s = s.upper()
    if R.random() < {"scam": 0.22, "spam": 0.3, "genuine": 0.08}[kind]:
        s = s + " " + pick(EMOJI)
    if R.random() < {"scam": 0.28, "spam": 0.28, "genuine": 0.2}[kind] and len(s) > 40:
        s = pick(["Dear Customer,", "Dear User,", "Hello,", "Hi,", "Dear {name},", "Hi {name},", "Attention:", "Notice:",
                  "VM-HDFCBK:", "AD-SBIINB:", "JD-AMZNIN -", "Dear Sir/Madam,"]).format(**ctx) + " " + s
    if R.random() < 0.1 and len(s) > 25:
        words = s.split(" ")
        i = R.randrange(len(words))
        w = words[i]
        if len(w) > 3 and w.isascii():
            j = R.randrange(len(w) - 1)
            words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
        s = " ".join(words)
    if R.random() < 0.08:
        s = s.replace(".", "").replace(",", "")
    return " ".join(s.split())


def generate_messages(n_scam: int = 2400, n_spam: int = 1500, n_genuine: int = 2400, seed: int = 7) -> list:
    R.seed(seed)
    rows, seen = [], set()
    for label, bank, n in (("scam", SCAM, n_scam), ("spam", SPAM, n_spam), ("genuine", GENUINE, n_genuine)):
        made, tries = 0, 0
        while made < n and tries < n * 30:
            tries += 1
            ctx = _ctx(label)
            skeleton = bank[R.randrange(len(bank))]
            text = _noise(_build(skeleton, ctx), label, ctx)
            if text in seen:
                continue
            seen.add(text)
            rows.append((text, label))
            made += 1
    R.shuffle(rows)
    return rows


# --------------------------------------------------------------------------------------
# URLs: label "safe" or "malicious"
# --------------------------------------------------------------------------------------
SAFE_DOMAINS = [
    "google.com", "mail.google.com", "accounts.google.com", "drive.google.com", "youtube.com", "wikipedia.org", "en.wikipedia.org", "amazon.in", "amazon.com",
    "flipkart.com", "paytm.com", "phonepe.com", "hdfcbank.com", "netbanking.hdfcbank.com", "sbi.co.in", "onlinesbi.sbi", "icicibank.com", "axisbank.com", "kotak.com",
    "irctc.co.in", "uidai.gov.in", "incometax.gov.in", "incometaxindiaefiling.gov.in", "digilocker.gov.in", "scholarships.gov.in", "ugc.gov.in", "aicte-india.org",
    "nptel.ac.in", "iitd.ac.in", "iitb.ac.in", "du.ac.in", "ignou.ac.in", "linkedin.com", "naukri.com", "internshala.com", "github.com", "stackoverflow.com",
    "medium.com", "microsoft.com", "login.microsoftonline.com", "office.com", "apple.com", "netflix.com", "spotify.com", "zoom.us", "whatsapp.com", "telegram.org",
    "x.com", "facebook.com", "instagram.com", "reddit.com", "bbc.com", "ndtv.com", "thehindu.com", "indianexpress.com", "zomato.com", "swiggy.com", "myntra.com",
    "bookmyshow.com", "makemytrip.com", "uber.com", "olacabs.com", "tcs.com", "infosys.com", "wipro.com", "accenture.com", "cognizant.com", "careers.google.com",
    "jobs.lever.co", "boards.greenhouse.io", "docs.python.org", "developer.mozilla.org", "pypi.org", "npmjs.com", "kaggle.com", "coursera.org", "udemy.com",
    "khanacademy.org", "nic.in", "india.gov.in", "mygov.in", "rbi.org.in", "npci.org.in", "epfindia.gov.in", "passportindia.gov.in", "cowin.gov.in", "dominos.co.in",
    "airtel.in", "jio.com", "vodafone.in", "bsnl.co.in", "paypal.com", "dropbox.com", "slack.com", "notion.so", "figma.com", "canva.com", "bhimupi.org.in",
    "timesofindia.indiatimes.com", "hindustantimes.com", "moneycontrol.com", "zerodha.com", "groww.in", "cricbuzz.com", "espncricinfo.com", "ted.com", "arxiv.org",
    "nature.com", "mit.edu", "stanford.edu", "ox.ac.uk", "iisc.ac.in", "bits-pilani.ac.in", "vit.ac.in", "nitt.edu", "aktu.ac.in", "mu.ac.in",
]
SAFE_PATHS = ["", "/", "/index.html", "/about", "/contact", "/careers", "/jobs", "/products", "/help", "/support", "/faq", "/blog", "/news", "/docs", "/pricing",
              "/account", "/login", "/signin", "/verify", "/orders", "/track", "/offers", "/search?q=laptops", "/wiki/Machine_learning", "/courses/{n}", "/p/itm{n}",
              "/dp/B0{x}", "/questions/{n}/how-to-use-regex", "/watch?v={x}", "/notice/{n}.pdf", "/en/home", "/personal/pay/cards", "/web/personal-banking",
              "/jobs/view/{n}", "/internships/python-internship", "/u/0/#inbox", "/issues/{n}", "/{x}/{x}", "/category/electronics?page=2", "/users/{n}/profile",
              "/admissions/2025", "/results", "/downloads/{x}.pdf", "/store/apps/details?id=com.example.app"]
MAL_BRANDS = ["google", "amazon", "microsoft", "paypal", "flipkart", "paytm", "phonepe", "sbi", "hdfc", "icici", "axis", "airtel", "jio", "netflix", "apple", "facebook",
              "instagram", "whatsapp", "irctc", "uidai", "aadhaar", "incometax", "pmkisan", "kbc", "tcs", "infosys", "wipro", "linkedin", "naukri", "dhl", "bluedart",
              "fedex", "amazonjobs", "googlecareers", "scholarship", "ugc", "aicte", "upi", "bhim", "kotak", "pnb", "canara", "yono", "electricity", "bsnl", "myntra"]
MAL_WORDS = ["login", "verify", "secure", "update", "kyc", "claim", "reward", "refund", "gift", "unlock", "support", "apply", "register", "winner", "account", "confirm",
             "bonus", "pay", "free", "offer", "cashback", "recharge", "lucky", "prize", "helpdesk", "alert", "billing", "suspended", "limited", "official", "portal", "yojana",
             "hiring", "careers", "jobs", "clearance", "delivery", "redelivery", "otp", "wallet", "bank", "netbanking", "install", "download"]
HOMOGLYPH = str.maketrans({"o": "0", "l": "1", "i": "1", "e": "3", "a": "4", "s": "5"})


def _typo(b: str) -> str:
    kind = R.random()
    if kind < 0.4:
        return b.translate(HOMOGLYPH) if b.translate(HOMOGLYPH) != b else b + "x"
    if kind < 0.7 and len(b) > 4:
        i = R.randrange(1, len(b) - 1)
        return b[:i] + b[i + 1:]
    if len(b) > 3:
        i = R.randrange(len(b) - 1)
        return b[:i] + b[i + 1] + b[i] + b[i + 2:]
    return b + b[-1]


def _safe_url() -> str:
    d = pick(SAFE_DOMAINS)
    path = pick(SAFE_PATHS).format(n=R.randint(100, 99999999), x=_rand_code(R.randint(6, 11)))
    sub = pick(["", "", "www.", "www.", "m.", "app."]) if d.count(".") == 1 else ""
    scheme = "http://" if R.random() < 0.07 else pick(["https://", "https://", ""])
    port = ":8443" if R.random() < 0.01 else ""
    if R.random() < 0.05:  # legit short links
        return pick(["https://youtu.be/", "https://amzn.to/", "https://lnkd.in/", "https://g.co/", "https://bit.ly/", "https://t.co/"]) + _rand_code(R.randint(5, 8))
    if R.random() < 0.03:  # small legit sites on cheap TLDs
        return f"https://{_rand_code(R.randint(5, 9)).lower()}-studio.{pick(['online', 'site', 'live'])}/about"
    return f"{scheme}{sub}{d}{port}{path}"


def _mal_url() -> str:
    b, w = pick(MAL_BRANDS), pick(MAL_WORDS)
    tld = pick(SCAM_TLD)
    scheme = pick(["http://", "https://", "https://", ""])
    k = R.random()
    path = pick(["", "/", f"/{w}", f"/{w}/{_rand_code(6)}", "/login.php", "/apply", f"/{w}?id={R.randint(100, 99999)}", "/verify/otp", "/form", "/claim", "/app.apk"])
    if k < 0.20:
        host = pick([f"{b}-{w}.{tld}", f"{w}-{b}.{tld}", f"{b}{w}.{tld}", f"{b}-{w}-{pick(MAL_WORDS)}.{tld}"])
    elif k < 0.32:
        host = f"{_typo(b)}{pick(['', '-' + w, '-login', '-secure'])}.{pick(['com', 'in', 'net', 'co', tld])}"
    elif k < 0.44:
        host = f"{b}.com.{w}-{pick(MAL_WORDS)}.{tld}" if R.random() < 0.5 else f"{w}.{b}.co.in.{pick(MAL_WORDS)}-{pick(MAL_WORDS)}.{tld}"
    elif k < 0.52:
        return f"http://{R.randint(11, 223)}.{R.randint(0, 255)}.{R.randint(0, 255)}.{R.randint(1, 254)}{pick([':8080', ':8888', '', ':81'])}/{pick([b, w, 'bank', 'pay'])}/{pick(['login.php', 'verify.html', 'kyc.php', 'index.php'])}"
    elif k < 0.60:
        return f"{pick(['https://', 'http://'])}{b}.com@{_rand_code(R.randint(5, 9)).lower()}-{w}.{tld}/{w}"
    elif k < 0.66:
        return f"https://xn--{_rand_code(R.randint(4, 7)).lower()}-{pick(['4ve', 'fsa', 'kva', '9ca'])}.{pick(['com', 'net', tld])}/{pick(['login', 'verify', ''])}"
    elif k < 0.76:
        host = f"{b}-{w}.{pick(['weebly.com', 'netlify.app', 'web.app', '000webhostapp.com', 'blogspot.com', 'pages.dev', 'wixsite.com', 'herokuapp.com', 'glitch.me'])}"
    elif k < 0.86:
        return f"{pick(['https://', 'http://', ''])}{pick(['bit.ly', 'tinyurl.com', 'cutt.ly', 'rb.gy', 'is.gd', 'shorturl.at'])}/{_rand_code(R.randint(5, 8))}"
    elif k < 0.93:
        host = f"{_rand_code(R.randint(8, 14)).lower()}.{tld}"
    else:
        host = f"secure-{w}-{b}-{pick(MAL_WORDS)}-{pick(MAL_WORDS)}.{pick(['com', 'net', 'info', tld])}"
    return f"{scheme}{host}{path}"


def generate_urls(n_safe: int = 3200, n_mal: int = 3200, seed: int = 11) -> list:
    R.seed(seed)
    rows, seen = [], set()
    for label, fn, n in (("safe", _safe_url, n_safe), ("malicious", _mal_url, n_mal)):
        made, tries = 0, 0
        while made < n and tries < n * 20:
            tries += 1
            u = fn()
            if u in seen:
                continue
            seen.add(u)
            rows.append((u, label))
            made += 1
    R.shuffle(rows)
    return rows
