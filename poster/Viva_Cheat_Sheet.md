# Viva cheat-sheet (based on your teachers' Unit V and Unit VI slides)

Say each point in one or two sentences, then show the worked example from the poster.

## Unit V: Basics of Investment

**1. Investment return** = gain (or loss) on an investment over a period, as a % of the amount invested. Total return = income + capital appreciation.
- Absolute return = (Vf - Vi)/Vi x 100. It ignores time. Eg: FD Rs 50,000 -> Rs 65,000 gives 30%.
- HPR (holding period return) = [Income + (Vf - Vi)]/Vi x 100, where income means dividends, coupons or interest.
  Eg: buy Rs 150, sell Rs 180, dividend Rs 10. HPR = (10 + 30)/150 x 100 = 26.67%.
- CAGR = (Vf/Vi)^(1/n) - 1. It is the yearly growth rate that smooths the years in between. It ignores volatility.
- Other types on the slides: real return (nominal - inflation), Sharpe ratio, excess return (Rp - benchmark).

**2. Uneven cash flows** = cash flows that are not equal every period (an annuity has equal payments).
- NPV = Sum of Ct/(1+k)^t - I. C = cash flow, k = discount rate, I = investment.
- Rule: NPV > 0 accept, NPV < 0 reject, NPV = 0 break-even.
- IRR = the discount rate at which NPV = 0. Accept if IRR > cost of capital.
- Eg: I = 1,00,000; flows 55,000, 80,000, 15,000; k = 10%. With PVIF 0.909, 0.826, 0.751: 49,995 + 66,080 + 11,265 - 1,00,000 = Rs 27,340. With exact discounting it is about Rs 27,385 (the slide rounds the PVIF). Either way NPV > 0, so accept.

**3. Compounding frequency** = how often interest is calculated and added to the principal. More frequent compounding means more interest, because interest starts earning interest sooner.
- A = P(1 + r/n)^(nt), interest = A - P. Continuous: A = P e^(rt). Effective annual rate = (1 + r/n)^n - 1.
- Eg: Rs 5,00,000 at 8% for 1 year. Yearly 5,40,000 (8.00%), half-yearly 5,40,800 (8.16%), quarterly 5,41,216.08 (8.2432%), monthly 5,41,499.75 (8.30%), daily 5,41,638.79 (8.3278%), continuous 5,41,643.53 (8.3287%).

**4. Economic equivalence** = two cash flows (at different times) are equal in value if they have the same value at a common point in time. Used to compare loan offers, lease vs purchase, payment options.
- FV = PV(1 + i)^n and PV = FV/(1 + i)^n (discounting).
- Eg: at 10%, Rs 1,000 today = Rs 1,331 after 3 years, and Rs 1,331 after 3 years is equivalent to Rs 1,000 today.

## Unit VI: Risk and Uncertainty

**1. Decision under risk and uncertainty**
- Risk = chance that an undesirable event occurs and causes a financial loss. Risk management = identify, assess and control risks.
- Types of risk faced by organisations: strategic (Kodak), compliance (new state, new laws), operational (paying Rs 1,00,000 instead of Rs 10,000), financial (prices, interest rates, exchange rates, liquidity, counterparty).
- Expected return X-bar = Sum Xi P(Xi). Variance = Sum d^2/n (or Sum d^2 P). SD sigma = sqrt(variance). CV = (sigma/mean) x 100.
- Higher SD or CV means riskier. SD is absolute risk; CV is risk per unit of return, so use it to compare securities with different average returns.
- Eg: returns 12, 18, 20, 15, 25 (%). Mean 18. Deviations -6, 0, 2, -3, 7, so squares sum to 98, variance 19.6, sigma 4.43%. CV = 4.43/18 = 24.6%.

**2. Risk premium** = extra return an investor expects for taking a risky asset compared with a risk-free asset: expected return on risky asset - return on risk-free asset.
- Sharpe ratio = (Rp - Rf)/sigma_p. Higher Sharpe means better return per unit of risk.
- Eg: Rp = 12%, Rf = 4%, sigma = 10%. Premium = 8%, Sharpe = 8/10 = 0.8.

**3. Portfolio diversification** = spreading money over different assets to reduce overall risk without necessarily reducing expected return. It works because assets do not all move the same way (correlation below +1).
- Covariance shows the direction of the relationship. Correlation rho = Cov/(sigma_X sigma_Y), always between -1 and +1 (+1 move together, 0 none, -1 opposite).
- Two assets: sigma_p^2 = w1^2 sigma1^2 + w2^2 sigma2^2 + 2 w1 w2 sigma1 sigma2 rho.
- Eg: w = 0.5, 0.5; sigma = 10%, 15%; rho = 0.25. Variance = 0.0025 + 0.005625 + 0.001875 = 0.01, so sigma_p = 10%. The portfolio is as safe as the safer asset X even though Y is riskier.

**4. Life insurance** = a contract. The policyholder pays premiums and the insurer pays the sum assured (death benefit) to the nominee on the insured's death. It transfers the risk of premature death.
- Types: term (death within the term only, cheapest, no maturity benefit), whole life (death whenever it occurs), endowment, money-back, ULIP, annuity.
- APV (actuarial present value) = S Sum v^k P(T = k), with v = 1/(1 + i). The APV is the net single premium.
- Eg: 3-year term, S = 2,00,000, i = 5%, P(T = 1, 2, 3) = 0.003, 0.0025, 0.002. APV = 2,00,000 (0.0028571 + 0.0022676 + 0.0017230) = Rs 1,370.48.
- The real (gross) premium is higher because insurers add expenses, risk margin, profit and sometimes tax.

**5. Endowment** = pays the sum assured if the insured dies within the term OR survives to maturity. It combines protection and savings, and the premium is higher than for term insurance.
- APV = S [ Sum v^k P(T = k) + v^n nPx ]. The first part is the PV of the death benefit; the second is the PV of the maturity benefit (nPx = chance of surviving n years).
- Eg: 20-year plan, S = 1,00,000. The beneficiaries get 1,00,000 if death occurs in the 20 years, and the policyholder gets 1,00,000 if they survive.

## Likely questions
- Why does more frequent compounding give more money? Interest itself starts earning interest sooner.
- What does NPV > 0 mean? The project's returns beat the cost of capital, so accept it.
- NPV vs IRR? NPV gives a rupee value and is best for the final decision; IRR gives a % and is compared with the cost of capital.
- SD vs CV? SD is absolute risk (volatility). CV is risk per unit of return, used to compare securities with different average returns.
- Why can diversification reduce risk? Imperfectly correlated assets offset each other's ups and downs.
- Endowment vs term insurance? Endowment also pays on survival (savings), so it costs more.
- Why is the real premium higher than the APV? Expenses, risk margin and profit loading.

## Warning: errors in the teacher's slides (so you are not surprised)
- Unit VI, 10-year endowment, S = 1,00,000, q = 0.005, i = 5%: the slide answers Rs 36,456.90, but the slide's own formula gives about Rs 62,172.65 (death part about 3,782.74 + survival part about 58,389.91). The poster does not use that example. If asked, say the formula is right and show the calculation.
- Unit V, CAGR of 50,000 -> 85,000 in 5 years: the slide says 11.22%, but (1.7)^(1/5) - 1 = 11.20%.
- Unit VI, slide 16 (stock costing Rs 120): the slide gives SD 5.9079; recomputing gives about 5.9073. This is just rounding.
