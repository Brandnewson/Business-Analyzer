import os
import yfinance as yf
import math
from millify import millify
import pandas as pd

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

def is_provided(field):
    # Ensure username or password is submitted
    if not request.form.get(field):
        return (f"must provide {field}", 400)


@app.route("/", methods =["GET"])
def index():
    return render_template("index.html")

@app.route("/analysis", methods = ["GET", "POST"])
def analysis():
    if request.method == "GET":
        return render_template("analysis.html")
    else:
        result_check = is_provided("symbol")
        if result_check is not None:
            return result_check
        symbol = request.form.get("symbol").upper()
        stock = yf.Ticker(symbol)
        stock.info
        stock.financials

        name = stock.info['shortName']
        desc = stock.info['longBusinessSummary']
        market_cap = millify(stock.info['marketCap'], precision=2)
        PE = round(stock.info['forwardPE'], 2)
        PB = round(stock.info['priceToBook'], 2)
        beta = round(stock.info['beta'], 2)

        gross_profit = millify(stock.info['grossProfits'], precision=2)
        revenue = millify(stock.info['totalRevenue'], precision=2)
        gross_margin = stock.info['grossProfits'] / stock.info['totalRevenue']
        net_income = millify(stock.info['netIncomeToCommon'], precision=2)
        net_margin = stock.info['netIncomeToCommon'] / stock.info['totalRevenue']
        gross_margin = millify(round(gross_margin * 100, 2), precision=2)
        net_margin = round(net_margin * 100, 2)

        DE = round(stock.info['debtToEquity'], 2)
        current_ratio = round(stock.info['currentRatio'], 2)
        cash = millify(stock.info['totalCash'], precision=2)
        cash_ps = millify(stock.info['totalCashPerShare'], precision=2)
        total_debt = millify(stock.info['totalDebt'], precision=2)
        currency = (stock.info['currency'])

        shares = millify(stock.info['sharesOutstanding'], precision=2)
        OCF = millify(stock.info['operatingCashflow'], precision=2)
        debt = millify(stock.info['totalDebt'], precision=2)
        price = round(stock.info['currentPrice'], 2)

        return render_template("analysed.html", symbol=symbol, name=name, desc=desc, market_cap=market_cap,
                                PE=PE, PB=PB, beta=beta, gross_profit=gross_profit, revenue=revenue,
                                 net_income=net_income, gross_margin=gross_margin, net_margin=net_margin, DE=DE,
                                 current_ratio=current_ratio, cash=cash, cash_ps=cash_ps, total_debt=total_debt,
                                 currency=currency, shares=shares, OCF=OCF, debt=debt,
                                 price=price)


@app.route("/dcf", methods = ["GET", "POST"])
def dcf():
    if request.method == "GET":

        return render_template("dcf.html", prompt="Please insert relevant data first")
    else:
        result_check = is_provided("symbol")
        if result_check is not None:
            return result_check

        #basics
        symbol = request.form.get("symbol").upper()
        gr_1 = float(request.form.get("gr_1"))
        gr_2 = float(request.form.get("gr_2"))
        gr_1 = gr_1*0.01
        gr_2 = gr_2*0.01
        grm_1 = float(request.form.get("grm_1"))
        grm_2 = float(request.form.get("grm_2"))
        grm_1 = grm_1*0.01
        grm_2 = grm_2*0.01
        ST_investment = request.form.get("ST_investment")
        ST_investment = float(ST_investment.replace(',', ''))
        stock = yf.Ticker(symbol)

        name = stock.info['shortName']
        beta = round(stock.info['beta'], 2)
        currency = (stock.info['currency'])

        #Pre-calculation values
        shares = stock.info['sharesOutstanding']
        shares_d = millify(stock.info['sharesOutstanding'], precision=2)
        OCF = stock.info['operatingCashflow']
        OCF_d = millify(stock.info['operatingCashflow'], precision=2)
        debt = stock.info['totalDebt']
        debt_d = millify(stock.info['totalDebt'], precision=2)
        price = round(stock.info['currentPrice'], 2)
        cash = stock.info['totalCash']
        cash_d = millify(stock.info['totalCash'], precision=2)

        cash_and_STI = (stock.info['totalCash']) + ST_investment
        cash_and_STI_d = millify(cash_and_STI, precision=2)


        #Cash Flow Projections(Low)
        cf_projected = (OCF+(OCF * gr_1))
        cf_p1 = (cf_projected + (gr_1 * cf_projected))
        cf_p2 = (cf_p1 + (gr_1 * cf_p1))
        cf_p3 = (cf_p2 + (gr_1 * cf_p2))
        cf_p4 = (cf_p3 + (gr_1 * cf_p3))
        cf_p5 = (cf_p4 + (gr_2 * cf_p4))
        cf_p6 = (cf_p5 + (gr_2 * cf_p5))
        cf_p7 = (cf_p6 + (gr_2 * cf_p6))
        cf_p8 = (cf_p7 + (gr_2 * cf_p7))
        cf_p9 = (cf_p8 + (gr_2 * cf_p8))

        #Cash Flow Projections(Mean)
        cfm_projected = (OCF+(OCF * grm_1))
        cfm_p1 = (cfm_projected + (grm_1 * cf_projected))
        cfm_p2 = (cfm_p1 + (grm_1 * cf_p1))
        cfm_p3 = (cfm_p2 + (grm_1 * cf_p2))
        cfm_p4 = (cfm_p3 + (grm_1 * cf_p3))
        cfm_p5 = (cfm_p4 + (grm_2 * cf_p4))
        cfm_p6 = (cfm_p5 + (grm_2 * cf_p5))
        cfm_p7 = (cfm_p6 + (grm_2 * cf_p6))
        cfm_p8 = (cfm_p7 + (grm_2 * cf_p7))
        cfm_p9 = (cfm_p8 + (grm_2 * cf_p8))

        #Calcuate Discount rate with Beta

        if beta > 1.6:
            d_rate = 0.09
        elif beta > 1.5:
            d_rate = 0.085
        elif beta > 1.4:
            d_rate = 0.08
        elif beta > 1.3:
            d_rate = 0.075
        elif beta > 1.2:
            d_rate = 0.07
        elif beta > 1.1:
            d_rate = 0.065
        elif beta > 1:
            d_rate = 0.06
        elif beta > 0.8:
            d_rate = 0.05
        elif beta < 0.8:
            d_rate = 0.05
        else:
            d_rate = 0.09

        d_rate_d = d_rate*100

        #Discount Factor
        #Next year
        discount_factor = 1/(1+d_rate)
        #Years onwards
        df_1 = discount_factor/(1+d_rate)
        df_2 = df_1/(1+d_rate)
        df_3 = df_2/(1+d_rate)
        df_4 = df_3/(1+d_rate)
        df_5 = df_4/(1+d_rate)
        df_6 = df_5/(1+d_rate)
        df_7 = df_6/(1+d_rate)
        df_8 = df_7/(1+d_rate)
        df_9 = df_8/(1+d_rate)

        #Discounted Value(Low)
        dv = cf_projected * discount_factor
        dv_1 = cf_p1*df_1
        dv_2 = cf_p2*df_2
        dv_3 = cf_p3*df_3
        dv_4 = cf_p4*df_4
        dv_5 = cf_p5*df_5
        dv_6 = cf_p6*df_6
        dv_7 = cf_p7*df_7
        dv_8 = cf_p8*df_8
        dv_9 = cf_p9*df_9

        #Discounted Value(Mean)
        dvm = cfm_projected * discount_factor
        dvm_1 = cfm_p1*df_1
        dvm_2 = cfm_p2*df_2
        dvm_3 = cfm_p3*df_3
        dvm_4 = cfm_p4*df_4
        dvm_5 = cfm_p5*df_5
        dvm_6 = cfm_p6*df_6
        dvm_7 = cfm_p7*df_7
        dvm_8 = cfm_p8*df_8
        dvm_9 = cfm_p9*df_9

        #pv of 10 yr cash flows(Low)
        pv = dv+dv_1+dv_2+dv_3+dv_4+dv_5+dv_6+dv_7+dv_8+dv_9
        pv_d = round(pv*0.0000001, 2)
        #pv of 10 yr cash flows(Mean)
        pvm = dvm+dvm_1+dvm_2+dvm_3+dvm_4+dvm_5+dvm_6+dvm_7+dvm_8+dvm_9
        pvm_d = round(pvm*0.0000001, 2)

        #Intrinsic Value before cash/debt(Low)
        intrinsic = pv/shares
        intrinsic_d = millify(intrinsic, precision=2)
        #Intrinsic Value before cash/debt(Mean)
        intrinsicm = pvm/shares
        intrinsicm_d = millify(intrinsicm, precision=2)

        #less debt per share
        less_debt = round(debt/shares, 2)

        #plus cash per share
        plus_cash = round((cash+ST_investment)/shares, 2)

        #final Intrinsic (Low)
        final_intrinsic = round(intrinsic + less_debt + plus_cash, 2)
        #Final Instrinsic (Mean)
        final_intrinsicm = round(intrinsicm + less_debt + plus_cash, 2)

        return render_template("dcf.html", symbol=symbol, name=name, beta=beta, currency=currency,
                                shares=shares_d, OCF=OCF_d, debt=debt_d, price=price, cash=cash_d,
                                cash_and_STI=cash_and_STI_d, final_intrinsic=final_intrinsic,
                                final_intrinsicm=final_intrinsicm, plus_cash=plus_cash, less_debt=less_debt,
                                intrinsicm=intrinsicm_d, intrinsic=intrinsic_d, d_rate=d_rate_d, pvm=pvm_d,
                                pv=pv_d
                                )



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return "sorry uwu"


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
