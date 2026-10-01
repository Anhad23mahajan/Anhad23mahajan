# Viva cheat-sheet (CA-III Financial Mathematics, Units V and VI)

Marks: Concept Clarity 1.5, Depth 1.5, Logical Organization 1, Neatness 6 (poster). Be ready to explain every box in 1 to 2 sentences and redo one example on the board.

## Unit V
- **Investment return:** gain as a % of money invested, (V1 - V0 + income)/V0. CAGR = (Vn/V0)^(1/n) - 1 is the steady yearly growth. Check: 10,000 to 14,641 in 4 yrs is 10% p.a.
- **Compounding frequency:** more compounding periods means more interest, but it has a ceiling, which is continuous compounding A = Pe^(rt). Effective rate = (1 + r/m)^m - 1. At 12% nominal: annual 12%, monthly 12.68%, continuous 12.75%.
- **Uneven cash flows:** cash flows differ each period, so discount each one separately and add. NPV = PV of inflows - cost; accept if NPV > 0. Here NPV is about +316.
- **Economic equivalence:** amounts at different dates are equivalent if they are worth the same at one common date at rate i. At 10%: 9,091 (1 yr ago) = 10,000 (today) = 12,100 (2 yrs later).

## Unit VI
- **Risk vs uncertainty:** risk means probabilities are known (use EMV); uncertainty means they are unknown (use maximax, maximin, minimax regret, Laplace). Regret = best payoff in that state - your payoff.
- **Risk premium:** E(R) - Rf, the extra return for taking risk (12% - 6% = 6%).
- **Diversification:** portfolio return is the weighted average, but portfolio risk is lower when correlation rho < 1. Unsystematic risk is removed by diversifying; systematic (market) risk is not. For two stocks with sigma = 20% and w = 50%, portfolio sigma is 20% at rho = 1, 14.1% at rho = 0, and 0% at rho = -1.
- **Life insurance:** pooling risk, with premium based on mortality q and interest i. 1-yr term NSP = S*q/(1+i) = 952.38. Real premium = NSP + expenses + profit.
- **Endowment:** pays on death within the term or on survival to maturity, so it is Term + Pure endowment. 2-yr NSP is about 90,748, mostly the savings part.

## Likely questions
1. Why is Rs 100 today worth more than Rs 100 next year? (It can earn interest.)
2. Which is better: 12% compounded monthly or 12.5% yearly? (Monthly effective is 12.68%, so monthly wins.)
3. What does NPV > 0 mean? (Returns beat the required rate, so accept.)
4. Why can diversification not remove all risk? (Systematic/market risk is common to all assets.)
5. Difference between maximin and minimax regret? (Pessimism about payoffs vs minimising regret.)
6. Difference between term and endowment? (Endowment also pays on survival.)
