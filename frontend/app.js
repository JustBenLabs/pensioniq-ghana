// ==========================================================
// PENSIONIQ GHANA
// FINAL FRONTEND APPLICATION LOGIC
// ==========================================================


// ==========================================================
// API CONFIGURATION
// ==========================================================

const API_BASE_URL =
    window.PENSIONIQ_API_BASE_URL;


// ==========================================================
// MAIN PENSION CALCULATOR ELEMENTS
// ==========================================================

const pensionForm =
    document.getElementById(
        "pension-form"
    );

const resultSection =
    document.getElementById(
        "result-section"
    );

const errorMessage =
    document.getElementById(
        "error-message"
    );

const calculateButton =
    document.getElementById(
        "calculate-button"
    );

const buttonText =
    document.getElementById(
        "button-text"
    );


// ==========================================================
// RETIREMENT COMPARISON ELEMENTS
// ==========================================================

const compareButton =
    document.getElementById(
        "compare-button"
    );

const comparisonResults =
    document.getElementById(
        "comparison-results"
    );


// ==========================================================
// MAIN PENSION CALCULATOR
// ==========================================================

pensionForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        hideError();

        resultSection.classList.add(
            "hidden"
        );

        setPensionLoading(true);


        // --------------------------------------------------
        // Read form values
        // --------------------------------------------------

        const dateOfBirth =
            document.getElementById(
                "dob"
            ).value;


        const retirementDate =
            document.getElementById(
                "retirement-date"
            ).value;


        const contributionMonths =
            Number(
                document.getElementById(
                    "contribution-months"
                ).value
            );


        const salary =
            Number(
                document.getElementById(
                    "salary"
                ).value
            );


        // --------------------------------------------------
        // Frontend validation
        // --------------------------------------------------

        if (
            !dateOfBirth ||
            !retirementDate
        ) {

            showError(
                "Please provide both your date of birth and retirement date."
            );

            setPensionLoading(false);

            return;
        }


        if (
            !Number.isFinite(
                contributionMonths
            )
            ||
            contributionMonths < 0
        ) {

            showError(
                "Contribution months must be zero or greater."
            );

            setPensionLoading(false);

            return;
        }


        if (
            !Number.isFinite(salary)
            ||
            salary <= 0
        ) {

            showError(
                "Please enter a valid annual salary."
            );

            setPensionLoading(false);

            return;
        }


        if (
            parseDateInput(retirementDate)
            <
            parseDateInput(dateOfBirth)
        ) {

            showError(
                "Retirement date cannot be before date of birth."
            );

            setPensionLoading(false);

            return;
        }


        // --------------------------------------------------
        // API request
        // --------------------------------------------------

        const requestData = {

            date_of_birth:
                dateOfBirth,

            retirement_date:
                retirementDate,

            contribution_months:
                contributionMonths,

            best_three_year_average_annual_salary:
                salary,

            qualifying_hazardous_employment:
                false

        };


        try {

            const response =
                await fetch(
                    `${API_BASE_URL}/benefits/retirement`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                requestData
                            )
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    extractApiError(
                        data,
                        "Unable to calculate pension."
                    )
                );

            }


            displayPensionResult(
    data,
    dateOfBirth,
    retirementDate,
    contributionMonths,
    salary
);

        }

        catch (error) {

            showError(
                error.message
            );

        }

        finally {

            setPensionLoading(
                false
            );

        }

    }
);


// ==========================================================
// DISPLAY MAIN PENSION RESULT
// ==========================================================

function displayPensionResult(
    data,
    dateOfBirth,
    retirementDate,
    contributionMonths,
    salary
) {

    // ------------------------------------------------------
    // Monthly pension
    // ------------------------------------------------------

    const monthlyBenefit =
        data.monthly_benefit;


    document.getElementById(
        "monthly-pension"
    ).textContent =
        monthlyBenefit !== null
        &&
        monthlyBenefit !== undefined
        ?
        formatCurrency(
            monthlyBenefit
        )
        :
        "Not Applicable";


    // ------------------------------------------------------
    // Benefit type
    // ------------------------------------------------------

    document.getElementById(
        "benefit-type"
    ).textContent =
        formatText(
            data.routed_benefit
        );


    // ------------------------------------------------------
    // Retirement age
    // ------------------------------------------------------

    const retirementAge =
        calculateAge(
            dateOfBirth,
            retirementDate
        );


    document.getElementById(
        "retirement-age"
    ).textContent =
        `${retirementAge} years`;


    // ------------------------------------------------------
    // Contribution months
    // ------------------------------------------------------

    document.getElementById(
        "result-contribution-months"
    ).textContent =
        contributionMonths
        .toLocaleString();


    // ------------------------------------------------------
    // Contribution years
    // ------------------------------------------------------

    const contributionYears =
        contributionMonths
        /
        12;


    document.getElementById(
        "contribution-years"
    ).textContent =
        `${contributionYears.toFixed(1)} years`;


    // ------------------------------------------------------
    // Pension right
    // ------------------------------------------------------

    const pensionRight =
        data.pension_right;


    if (
        pensionRight !== null
        &&
        pensionRight !== undefined
    ) {

        const pensionRightPercentage =
            Number(
                pensionRight
            )
            *
            100;


        document.getElementById(
            "pension-right"
        ).textContent =
            `${pensionRightPercentage.toFixed(3)}%`;

    }

    else {

        document.getElementById(
            "pension-right"
        ).textContent =
            "Not Applicable";

    }


    // ------------------------------------------------------
    // Calculation status
    // ------------------------------------------------------

    document.getElementById(
        "calculation-status"
    ).textContent =
        formatText(
            data.calculation_status
        );


    // ------------------------------------------------------
    // Eligibility badge
    // ------------------------------------------------------

    const eligibilityBadge =
        document.getElementById(
            "eligibility-badge"
        );


    if (data.eligible) {

        eligibilityBadge.textContent =
            "Eligible";

    }

    else {

        eligibilityBadge.textContent =
            "Not Eligible";

    }


    // ------------------------------------------------------
    // Contribution progress
    // ------------------------------------------------------

    updateContributionProgress(
        contributionMonths
    );

    displayCalculationBreakdown(
    data,
    salary,
    contributionMonths
);


    // ------------------------------------------------------
    // Show result
    // ------------------------------------------------------

    resultSection.classList.remove(
        "hidden"
    );


    resultSection.scrollIntoView(
        {
            behavior: "smooth",
            block: "start"
        }
    );

}

// ==========================================================
// CALCULATION TRANSPARENCY
// ==========================================================

function displayCalculationBreakdown(
    data,
    salary,
    contributionMonths
) {

    const annualSalary =
    Number(salary);

    const monthlySalaryBasis =
    data.monthly_salary_basis !== null
    &&
    data.monthly_salary_basis !== undefined
        ? Number(
            data.monthly_salary_basis
        )
        : null;


    const pensionRight =
        data.pension_right !== null
        &&
        data.pension_right !== undefined
            ? Number(data.pension_right)
            : null;


    const monthlyBenefit =
        data.monthly_benefit !== null
        &&
        data.monthly_benefit !== undefined
            ? Number(data.monthly_benefit)
            : null;


    const retirementAge =
        document.getElementById(
            "retirement-age"
        ).textContent.trim();


    document.getElementById(
        "calc-annual-salary"
    ).textContent =
        formatBreakdownCurrency(
            annualSalary
        );


    document.getElementById(
    "calc-monthly-salary"
).textContent =
    monthlySalaryBasis !== null
    &&
    Number.isFinite(
        monthlySalaryBasis
    )
        ?
        formatBreakdownCurrency(
            monthlySalaryBasis
        )
        :
        "Not Applicable";


    document.getElementById(
        "calc-contribution-months"
    ).textContent =
        Number(
            contributionMonths
        ).toLocaleString();


    document.getElementById(
        "calc-retirement-age"
    ).textContent =
        retirementAge;


    if (
        pensionRight !== null
        &&
        Number.isFinite(pensionRight)
    ) {

        document.getElementById(
            "calc-pension-right"
        ).textContent =
            `${(
                pensionRight * 100
            ).toFixed(3)}%`;

    }
    else {

        document.getElementById(
            "calc-pension-right"
        ).textContent =
            "Not Applicable";

    }
    displayPensionRightExplanation(
    contributionMonths,
    pensionRight
);


    const pensionBeforeAgeFactor =
        monthlySalaryBasis
        *
        (
            pensionRight ?? 0
        );


    const retirementFactor =
    data.retirement_age_factor !== null
    &&
    data.retirement_age_factor !== undefined
        ? Number(
            data.retirement_age_factor
        )
        : null;


    if (
        retirementFactor !== null
        &&
        Number.isFinite(retirementFactor)
    ) {

        document.getElementById(
            "calc-retirement-factor"
        ).textContent =
            `${(
                retirementFactor * 100
            ).toFixed(1)}%`;

    }
    else {

        document.getElementById(
            "calc-retirement-factor"
        ).textContent =
            "Not Applicable";

    }

    const retirementFactorExplanation =
    document.getElementById(
        "retirement-factor-explanation"
    );


    const retirementAgeNumber =
    Number(
        retirementAge
    );


if (
    retirementFactor !== null
    &&
    Number.isFinite(
        retirementFactor
    )
) {

    if (
        retirementAgeNumber < 60
        &&
        retirementFactor === 1
    ) {

        retirementFactorExplanation.textContent =
            `The calculation applies a 100% retirement-age factor at age `
            +
            `${retirementAgeNumber}. No early-retirement reduction was `
            +
            `applied under the benefit route returned by the actuarial engine.`;

    }
    else if (
        retirementAgeNumber < 60
    ) {

        retirementFactorExplanation.textContent =
            `Retirement at age ${retirementAgeNumber} applies a `
            +
            `${(
                retirementFactor * 100
            ).toFixed(1)}% retirement-age factor in this calculation.`;

    }
    else {

        retirementFactorExplanation.textContent =
            "Age 60 is the full pension age, so a 100% retirement-age factor is applied.";

    }

}
else {

    retirementFactorExplanation.textContent =
        "A retirement-age adjustment is not applicable for this result.";

}


    const formulaElement =
        document.getElementById(
            "calc-formula"
        );


    if (
        pensionRight !== null
        &&
        retirementFactor !== null
        &&
        monthlyBenefit !== null
    ) {

        formulaElement.textContent =
            `${formatBreakdownCurrency(
                monthlySalaryBasis
            )} \u00D7 `
            +
            `${(
                pensionRight * 100
            ).toFixed(3)}% \u00D7 `
            +
            `${(
                retirementFactor * 100
            ).toFixed(1)}%`;

    }
    else {

        formulaElement.textContent =
            "Monthly pension calculation "
            +
            "is not applicable for this result.";

    }


    document.getElementById(
        "calc-monthly-pension"
    ).textContent =
        monthlyBenefit !== null
        &&
        Number.isFinite(monthlyBenefit)
            ?
            formatBreakdownCurrency(
                monthlyBenefit
            )
            :
            "Not Applicable";
}

// ==========================================================
// PENSION RIGHT EXPLANATION
// ==========================================================

function displayPensionRightExplanation(
    contributionMonths,
    pensionRight
) {

    const months =
        Number(
            contributionMonths
        );

    const explanation =
        document.getElementById(
            "pension-right-explanation-text"
        );

    const formula =
        document.getElementById(
            "pension-right-formula"
        );


    if (
        !Number.isFinite(months)
    ) {

        explanation.textContent =
            "Contribution information is unavailable.";

        formula.textContent =
            "-";

        return;
    }


    // Less than 180 months
    if (months < 180) {

        const monthsRemaining =
            180 - months;

        explanation.textContent =
            `You currently have ${months.toLocaleString()} `
            +
            `contribution months. The ordinary monthly `
            +
            `pension route in this PensionIQ model `
            +
            `requires at least 180 contribution months.`;

        formula.textContent =
            `${monthsRemaining.toLocaleString()} `
            +
            `more contribution month`
            +
            `${monthsRemaining === 1 ? "" : "s"} `
            +
            `to reach 180 months.`;

        return;
    }


    // Maximum pension right
    if (months >= 420) {

        explanation.textContent =
            `You have ${months.toLocaleString()} `
            +
            `contribution months. The maximum pension `
            +
            `right used by this model is 60%.`;

        formula.textContent =
            "420 or more contribution months → 60.000%";

        return;
    }


    // Between 180 and 419 months
    const additionalMonths =
        months - 180;

    const pensionRightPercentage =
        pensionRight !== null
        &&
        Number.isFinite(
            pensionRight
        )
            ?
            pensionRight * 100
            :
            null;


    explanation.textContent =
        `The first 180 contribution months provide `
        +
        `a pension right of 37.5%. Each additional `
        +
        `contribution month adds 0.09375 percentage `
        +
        `points. You have ${additionalMonths.toLocaleString()} `
        +
        `additional month`
        +
        `${additionalMonths === 1 ? "" : "s"}.`;


    if (
        pensionRightPercentage !== null
    ) {

        formula.textContent =
            `37.5% + `
            +
            `(${additionalMonths.toLocaleString()} × 0.09375%) `
            +
            `= ${pensionRightPercentage.toFixed(3)}%`;

    }
    else {

        formula.textContent =
            `37.5% + `
            +
            `(${additionalMonths.toLocaleString()} × 0.09375%)`;

    }
}


function formatBreakdownCurrency(
    value
) {

    const numericValue =
        Number(value);


    if (
        !Number.isFinite(numericValue)
    ) {

        return "GH\u00A20.00";

    }


    return (
        "GH\u00A2"
        +
        numericValue.toLocaleString(
            "en-GH",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )
    );
}

// ==========================================================
// CONTRIBUTION PROGRESS
// ==========================================================

function updateContributionProgress(
    contributionMonths
) {

    const minimumMonths =
        180;

    const maximumMonths =
        420;


    let progress = 0;


    if (
        contributionMonths >=
        minimumMonths
    ) {

        progress =
            (
                (
                    contributionMonths
                    -
                    minimumMonths
                )
                /
                (
                    maximumMonths
                    -
                    minimumMonths
                )
            )
            *
            100;

    }


    progress =
        Math.max(
            0,
            Math.min(
                progress,
                100
            )
        );


    document.getElementById(
        "progress-bar"
    ).style.width =
        `${progress}%`;


    document.getElementById(
        "progress-percentage"
    ).textContent =
        `${progress.toFixed(1)}%`;


    document.getElementById(
        "progress-current-months"
    ).textContent =
        `${contributionMonths.toLocaleString()} months`;


    const progressMessage =
        document.getElementById(
            "progress-message"
        );


    if (
        contributionMonths <
        minimumMonths
    ) {

        const monthsNeeded =
            minimumMonths
            -
            contributionMonths;


        progressMessage.textContent =
            `${monthsNeeded} additional months needed to reach the minimum pension threshold`;

    }

    else if (
        contributionMonths <
        maximumMonths
    ) {

        const monthsRemaining =
            maximumMonths
            -
            contributionMonths;


        const yearsRemaining =
            monthsRemaining
            /
            12;


        progressMessage.textContent =
            `${monthsRemaining} months (${yearsRemaining.toFixed(1)} years) to the maximum pension-right threshold`;

    }

    else {

        progressMessage.textContent =
            "Maximum pension-right threshold reached";

    }

}


// ==========================================================
// RETIREMENT AGE COMPARISON
// ==========================================================

compareButton.addEventListener(
    "click",
    compareRetirementAges
);


async function compareRetirementAges() {

    hideError();


    // ------------------------------------------------------
    // Read comparison inputs
    // ------------------------------------------------------

    const dateOfBirth =
        document.getElementById(
            "comparison-dob"
        ).value;


    const contributionMonths =
        Number(
            document.getElementById(
                "months-at-55"
            ).value
        );


    const salary =
        Number(
            document.getElementById(
                "comparison-salary"
            ).value
        );


    const sex =
        document.getElementById(
            "comparison-sex"
        ).value;


    const annualDiscountRatePercent =
        Number(
            document.getElementById(
                "discount-rate"
            ).value
        );


    const annualDiscountRate =
        annualDiscountRatePercent
        /
        100;


    const projectionAge =
        Number(
            document.getElementById(
                "projection-age"
            ).value
        );


    // ------------------------------------------------------
    // Validation
    // ------------------------------------------------------

    if (!dateOfBirth) {

        showError(
            "Please enter a date of birth for the retirement comparison."
        );

        return;
    }


    if (
        !Number.isFinite(
            contributionMonths
        )
        ||
        contributionMonths < 0
    ) {

        showError(
            "Contribution months at age 55 must be zero or greater."
        );

        return;
    }


    if (
        !Number.isFinite(salary)
        ||
        salary <= 0
    ) {

        showError(
            "Please enter a valid salary for the retirement comparison."
        );

        return;
    }


    if (
        ![
            "Male",
            "Female"
        ].includes(sex)
    ) {

        showError(
            "Please select Male or Female."
        );

        return;
    }


    if (
        !Number.isFinite(
            annualDiscountRatePercent
        )
        ||
        annualDiscountRatePercent < 0
    ) {

        showError(
            "Discount rate cannot be negative."
        );

        return;
    }


    if (
        !Number.isInteger(
            projectionAge
        )
        ||
        projectionAge <= 60
        ||
        projectionAge > 100
    ) {

        showError(
            "Projection age must be a whole number between 61 and 100."
        );

        return;
    }


    setComparisonLoading(
        true
    );


    try {

        // ==================================================
        // ORDINARY RETIREMENT COMPARISON
        // ==================================================

        const response =
            await fetch(
                `${API_BASE_URL}/benefits/retirement-comparison`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {

                                date_of_birth:
                                    dateOfBirth,

                                contribution_months_at_55:
                                    contributionMonths,

                                best_three_year_average_annual_salary:
                                    salary,

                                qualifying_hazardous_employment:
                                    false

                            }
                        )
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                extractApiError(
                    data,
                    "Unable to compare retirement scenarios."
                )
            );

        }


        // --------------------------------------------------
        // Display normal comparison
        // --------------------------------------------------

        displayComparison(
            data.scenarios,
            annualDiscountRate,
            projectionAge
        );


        // ==================================================
        // MORTALITY-ADJUSTED EPV COMPARISON
        // ==================================================

        await loadEPVComparison(

            dateOfBirth,

            contributionMonths,

            salary,

            sex,

            annualDiscountRatePercent,

            projectionAge

        );


        comparisonResults.classList.remove(
            "hidden"
        );


        comparisonResults.scrollIntoView(
            {
                behavior: "smooth",
                block: "start"
            }
        );

    }

    catch (error) {

        showError(
            error.message
        );

    }

    finally {

        setComparisonLoading(
            false
        );

    }

}


// ==========================================================
// DISPLAY ORDINARY RETIREMENT COMPARISON
// ==========================================================

function displayComparison(
    scenarios,
    annualDiscountRate,
    projectionAge
) {

    displayDetailedComparisonTable(
        scenarios
    );


    displayRetirementChart(
        scenarios
    );


    displayBreakEvenAnalysis(
        scenarios
    );


    displayPresentValueAnalysis(
        scenarios,
        annualDiscountRate,
        projectionAge
    );


    decorateOrdinaryComparisonInsights(
        scenarios,
        annualDiscountRate,
        projectionAge
    );

}


// ==========================================================
// DETAILED COMPARISON TABLE
// ==========================================================

function displayDetailedComparisonTable(
    scenarios
) {

    const tableBody =
        document.getElementById(
            "comparison-body"
        );


    tableBody.replaceChildren();


    scenarios.forEach(
        scenario => {

            const row =
                document.createElement(
                    "tr"
                );


            const pensionRight =
                scenario.pension_right
                ?
                (
                    Number(
                        scenario.pension_right
                    )
                    *
                    100
                ).toFixed(3)
                +
                "%"
                :
                "N/A";


            const pension =
                scenario.monthly_benefit
                ?
                formatCurrency(
                    scenario.monthly_benefit
                )
                :
                "Not Applicable";


            const ageCell =
    document.createElement(
        "td"
    );

ageCell.textContent =
    String(
        scenario.retirement_age
    );


const monthsCell =
    document.createElement(
        "td"
    );

monthsCell.textContent =
    Number(
        scenario.contribution_months
    ).toLocaleString();


const rightCell =
    document.createElement(
        "td"
    );

rightCell.textContent =
    pensionRight;


const pensionCell =
    document.createElement(
        "td"
    );

pensionCell.textContent =
    pension;


const statusCell =
    document.createElement(
        "td"
    );


if (
    scenario.retirement_age === 60
) {

    const recommendedTag =
        document.createElement(
            "span"
        );

    recommendedTag.className =
        "recommended-tag";

    recommendedTag.textContent =
        "Full Pension Age";

    statusCell.appendChild(
        recommendedTag
    );

}
else {

    statusCell.textContent =
        formatText(
            scenario.benefit_type
        );

}


row.append(
    ageCell,
    monthsCell,
    rightCell,
    pensionCell,
    statusCell
);


            tableBody.appendChild(
                row
            );

        }
    );

}


// ==========================================================
// MONTHLY PENSION CHART
// ==========================================================

function displayRetirementChart(
    scenarios
) {

    const chart =
        document.getElementById(
            "retirement-chart"
        );


    chart.replaceChildren();


    const pensionValues =
        scenarios.map(
            scenario =>
                Number(
                    scenario.monthly_benefit
                    ||
                    0
                )
        );


    const maximumPension =
        pensionValues.length
        ?
        Math.max(
            ...pensionValues
        )
        :
        0;


    scenarios.forEach(
        scenario => {

            const pension =
                Number(
                    scenario.monthly_benefit
                    ||
                    0
                );


            const width =
                maximumPension > 0
                ?
                (
                    pension
                    /
                    maximumPension
                )
                *
                100
                :
                0;


            const row =
                document.createElement(
                    "div"
                );


            row.className =
                `chart-row ${
                    scenario.retirement_age === 60
                    ?
                    "age-60"
                    :
                    ""
                }`;


            const ageLabel =
    document.createElement(
        "div"
    );

ageLabel.className =
    "chart-age";

ageLabel.textContent =
    `Age ${scenario.retirement_age}`;


const track =
    document.createElement(
        "div"
    );

track.className =
    "chart-track";


const bar =
    document.createElement(
        "div"
    );

bar.className =
    "chart-bar";

bar.style.width =
    `${width}%`;


track.appendChild(
    bar
);


const amount =
    document.createElement(
        "div"
    );

amount.className =
    "chart-amount";

amount.textContent =
    (
        pension > 0
    )
        ?
        formatCurrency(
            pension
        )
        :
        "N/A";


row.append(
    ageLabel,
    track,
    amount
);

            chart.appendChild(
                row
            );

        }
    );

}


// ==========================================================
// BREAK-EVEN ANALYSIS
// ==========================================================

function displayBreakEvenAnalysis(
    scenarios
) {

    const container =
        document.getElementById(
            "breakeven-results"
        );


    container.replaceChildren();


    const age60Scenario =
        scenarios.find(
            scenario =>
                scenario.retirement_age
                ===
                60
        );


    if (
        !age60Scenario
        ||
        !age60Scenario.monthly_benefit
    ) {

        const unavailableMessage =
    document.createElement(
        "p"
    );

unavailableMessage.textContent =
    "Age 60 pension data is unavailable.";


container.appendChild(
    unavailableMessage
);

        return;

    }


    const age60Pension =
        Number(
            age60Scenario.monthly_benefit
        );


    scenarios
        .filter(
            scenario =>
                scenario.retirement_age
                <
                60
        )
        .forEach(
            scenario => {

                const earlyPension =
                    Number(
                        scenario.monthly_benefit
                        ||
                        0
                    );


                const breakEvenAge =
                    calculateBreakEvenAge(

                        scenario.retirement_age,

                        earlyPension,

                        age60Pension

                    );


                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "breakeven-item";


                let resultText;

                let explanation;


                if (
                    breakEvenAge
                    ===
                    null
                ) {

                    resultText =
                        "No crossover";


                    explanation =
                        "Age 60 does not catch up before age 100.";

                }

                else {

                    resultText =
                        formatAge(
                            breakEvenAge
                        );


                    explanation =
                        `Age ${scenario.retirement_age} versus age 60`;

                }


                const ageLabel =
    document.createElement(
        "span"
    );

ageLabel.textContent =
    `Retire at Age ${scenario.retirement_age}`;


const resultValue =
    document.createElement(
        "strong"
    );

resultValue.textContent =
    resultText;


const explanationText =
    document.createElement(
        "small"
    );

explanationText.textContent =
    explanation;


card.append(
    ageLabel,
    resultValue,
    explanationText
);

                container.appendChild(
                    card
                );

            }
        );

}


// ==========================================================
// BREAK-EVEN CALCULATION
// ==========================================================

function calculateBreakEvenAge(
    earlyRetirementAge,
    earlyMonthlyPension,
    age60MonthlyPension
) {

    if (
        earlyMonthlyPension <= 0
        ||
        age60MonthlyPension <= 0
    ) {

        return null;

    }


    if (
        age60MonthlyPension
        <=
        earlyMonthlyPension
    ) {

        return null;

    }


    const earlyStartMonth =
        earlyRetirementAge
        *
        12;


    const age60StartMonth =
        60
        *
        12;


    const maximumMonth =
        100
        *
        12;


    let earlyTotal =
        0;


    let age60Total =
        0;


    // Payments assumed monthly in arrears.
    for (
        let month =
            earlyStartMonth + 1;

        month <= maximumMonth;

        month++
    ) {

        earlyTotal +=
            earlyMonthlyPension;


        if (
            month >
            age60StartMonth
        ) {

            age60Total +=
                age60MonthlyPension;

        }


        if (
            month >
            age60StartMonth
            &&
            age60Total
            >=
            earlyTotal
        ) {

            return (
                month
                /
                12
            );

        }

    }


    return null;

}


// ==========================================================
// ORDINARY PRESENT VALUE ANALYSIS
// ==========================================================

function displayPresentValueAnalysis(
    scenarios,
    annualDiscountRate,
    projectionAge
) {

    const container =
        document.getElementById(
            "pv-results"
        );


    container.replaceChildren();


    const monthlyRate =
        Math.pow(
            1
            +
            annualDiscountRate,
            1 / 12
        )
        -
        1;


    const results =
        scenarios.map(
            scenario => {

                const presentValue =
                    calculatePensionPresentValue(

                        scenario.retirement_age,

                        Number(
                            scenario.monthly_benefit
                            ||
                            0
                        ),

                        projectionAge,

                        monthlyRate

                    );


                return {

                    ...scenario,

                    presentValue:
                        presentValue

                };

            }
        );


    const validResults =
        results.filter(
            item =>
                item.presentValue
                >
                0
        );


    const maximumPV =
        validResults.length
        ?
        Math.max(
            ...validResults.map(
                item =>
                    item.presentValue
            )
        )
        :
        0;


    results.forEach(
        scenario => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "pv-item";


            const isHighest =
                maximumPV > 0
                &&
                Math.abs(
                    scenario.presentValue
                    -
                    maximumPV
                )
                <
                0.01;


            const ageLabel =
    document.createElement(
        "span"
    );

ageLabel.textContent =
    `Retire at Age ${scenario.retirement_age}`;


const value =
    document.createElement(
        "strong"
    );

value.textContent =
    (
        scenario.presentValue > 0
    )
        ?
        formatCurrency(
            scenario.presentValue
        )
        :
        "N/A";


const description =
    document.createElement(
        "small"
    );

description.textContent =
    isHighest
        ?
        "Highest present value under these assumptions"
        :
        "Value measured at age 55";


card.append(
    ageLabel,
    value,
    description
);
            container.appendChild(
                card
            );

        }
    );


    document.getElementById(
        "pv-assumption-text"
    ).textContent =
        `Future pension payments are discounted to age 55 using an annual effective discount rate of ${(annualDiscountRate * 100).toFixed(2)}%, with payments projected through age ${projectionAge}. Mortality and pension indexation are not included in this section.`;

}


// ==========================================================
// ORDINARY PRESENT VALUE CALCULATION
// ==========================================================

function calculatePensionPresentValue(
    retirementAge,
    monthlyPension,
    projectionAge,
    monthlyDiscountRate
) {

    if (
        monthlyPension <= 0
        ||
        projectionAge <=
        retirementAge
    ) {

        return 0;

    }


    const valuationAge =
        55;


    const firstPaymentMonth =
        (
            retirementAge
            -
            valuationAge
        )
        *
        12
        +
        1;


    const finalPaymentMonth =
        (
            projectionAge
            -
            valuationAge
        )
        *
        12;


    let presentValue =
        0;


    for (
        let month =
            firstPaymentMonth;

        month <=
            finalPaymentMonth;

        month++
    ) {

        const discountFactor =
            Math.pow(
                1
                +
                monthlyDiscountRate,
                month
            );


        presentValue +=
            monthlyPension
            /
            discountFactor;

    }


    return presentValue;

}


// ==========================================================
// MORTALITY-ADJUSTED EPV API REQUEST
// ==========================================================

async function loadEPVComparison(
    dateOfBirth,
    contributionMonths,
    salary,
    sex,
    annualDiscountRatePercent,
    projectionAge
) {

    const response =
        await fetch(
            `${API_BASE_URL}/benefits/retirement-epv-comparison`,
            {
                method:
                    "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(
                        {

                            date_of_birth:
                                dateOfBirth,

                            contribution_months_at_55:
                                contributionMonths,

                            best_three_year_average_annual_salary:
                                salary,

                            sex:
                                sex,

                            annual_discount_rate_percent:
                                annualDiscountRatePercent,

                            projection_age:
                                projectionAge,

                            qualifying_hazardous_employment:
                                false

                        }
                    )
            }
        );


    const data =
        await response.json();


    if (!response.ok) {

        throw new Error(
            extractApiError(
                data,
                "Unable to calculate mortality-adjusted retirement values."
            )
        );

    }


    displayEPVComparison(
        data
    );

}


// ==========================================================
// DISPLAY MORTALITY-ADJUSTED EPV
// ==========================================================

function displayEPVComparison(
    data
) {

    const scenarios =
        data.scenarios
        ||
        [];


    displayEPVTable(
        scenarios
    );


    displayEPVChart(
        scenarios
    );


    displayEPVSummary(
        scenarios
    );


    displayMortalityBasis(
        data
    );


    decorateEPVComparisonInsights(
        scenarios
    );

}


// ==========================================================
// EPV TABLE
// ==========================================================

function displayEPVTable(
    scenarios
) {

    const tableBody =
        document.getElementById(
            "epv-table-body"
        );


    tableBody.replaceChildren();


    scenarios.forEach(
        scenario => {

            const row =
                document.createElement(
                    "tr"
                );


            const monthlyPension =
                scenario.monthly_pension
                ?
                formatCurrency(
                    scenario.monthly_pension
                )
                :
                "N/A";


            const pensionRight =
                scenario.pension_right
                ?
                (
                    Number(
                        scenario.pension_right
                    )
                    *
                    100
                ).toFixed(3)
                +
                "%"
                :
                "N/A";


            const epv =
                scenario.expected_present_value
                ?
                formatCurrency(
                    scenario.expected_present_value
                )
                :
                "N/A";


            const ageCell =
    document.createElement(
        "td"
    );

ageCell.textContent =
    String(
        scenario.retirement_age
    );


const pensionCell =
    document.createElement(
        "td"
    );

pensionCell.textContent =
    monthlyPension;


const rightCell =
    document.createElement(
        "td"
    );

rightCell.textContent =
    pensionRight;


const epvCell =
    document.createElement(
        "td"
    );

epvCell.textContent =
    epv;


row.append(
    ageCell,
    pensionCell,
    rightCell,
    epvCell
);

            tableBody.appendChild(
                row
            );

        }
    );

}


// ==========================================================
// EPV CHART
// ==========================================================

function displayEPVChart(
    scenarios
) {

    const chart =
        document.getElementById(
            "epv-chart"
        );


    chart.replaceChildren();


    const epvValues =
        scenarios.map(
            scenario =>
                Number(
                    scenario.expected_present_value
                    ||
                    0
                )
        );


    const maximumEPV =
        epvValues.length
        ?
        Math.max(
            ...epvValues
        )
        :
        0;


    scenarios.forEach(
        scenario => {

            const epv =
                Number(
                    scenario.expected_present_value
                    ||
                    0
                );


            const width =
                maximumEPV > 0
                ?
                (
                    epv
                    /
                    maximumEPV
                )
                *
                100
                :
                0;


            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "epv-chart-row";


            const ageLabel =
    document.createElement(
        "div"
    );

ageLabel.className =
    "epv-chart-age";

ageLabel.textContent =
    `Age ${scenario.retirement_age}`;


const track =
    document.createElement(
        "div"
    );

track.className =
    "epv-chart-track";


const bar =
    document.createElement(
        "div"
    );

bar.className =
    "epv-chart-bar";

bar.style.width =
    `${width}%`;


track.appendChild(
    bar
);


const value =
    document.createElement(
        "div"
    );

value.className =
    "epv-chart-value";

value.textContent =
    (
        epv > 0
    )
        ?
        formatCurrency(
            epv
        )
        :
        "N/A";


row.append(
    ageLabel,
    track,
    value
);


            chart.appendChild(
                row
            );

        }
    );

}


// ==========================================================
// EPV SUMMARY
// ==========================================================

function displayEPVSummary(
    scenarios
) {

    const summary =
        document.getElementById(
            "epv-summary"
        );




    const validScenarios =
        scenarios.filter(
            scenario =>
                Number(
                    scenario.expected_present_value
                    ||
                    0
                )
                >
                0
        );


    if (
        validScenarios.length
        ===
        0
    ) {

        const label =
    document.createElement(
        "span"
    );

label.textContent =
    "Mortality-adjusted actuarial analysis";


const value =
    document.createElement(
        "strong"
    );

value.textContent =
    "No EPV available";


const explanation =
    document.createElement(
        "p"
    );

explanation.textContent =
    (
        "No eligible monthly pension scenario " +
        "was available for this comparison."
    );


summary.append(
    label,
    value,
    explanation
);

        return;

    }


    const highest =
        validScenarios.reduce(
            (
                currentHighest,
                scenario
            ) => {

                return (
                    Number(
                        scenario.expected_present_value
                    )
                    >
                    Number(
                        currentHighest.expected_present_value
                    )
                )
                ?
                scenario
                :
                currentHighest;

            }
        );


    const label =
    document.createElement(
        "span"
    );

label.textContent =
    (
        "Highest mortality-adjusted EPV " +
        "under these assumptions"
    );


const value =
    document.createElement(
        "strong"
    );

value.textContent =
    formatCurrency(
        highest.expected_present_value
    );


const explanation =
    document.createElement(
        "p"
    );

explanation.textContent =
    (
        `Retirement age ${highest.retirement_age}. ` +
        "This result depends on the selected mortality, " +
        "discount-rate and projection assumptions and " +
        "should not be interpreted as a universal " +
        "recommendation."
    );


summary.append(
    label,
    value,
    explanation
);
}


// ==========================================================
// MORTALITY BASIS
// ==========================================================

function displayMortalityBasis(
    data
) {

    const basis =
        data.mortality_basis;


    const element =
        document.getElementById(
            "mortality-basis-text"
        );


    if (!basis) {

        element.textContent =
            "Mortality basis information is unavailable.";

        return;

    }


    element.textContent =
        `${basis.source}. `
        +
        `Population: ${basis.population}. `
        +
        `Sex: ${basis.sex}. `
        +
        `Reference year: ${basis.reference_year}. `
        +
        `Basis: ${basis.model_type}. `
        +
        `This is Ghana population mortality and not an official SSNIT pensioner mortality table.`;

}


// ==========================================================
// DATE HELPERS
// ==========================================================

function parseDateInput(
    dateString
) {

    const [
        year,
        month,
        day
    ] =
        dateString
        .split("-")
        .map(Number);


    return new Date(
        year,
        month - 1,
        day
    );

}


function calculateAge(
    birthDateString,
    targetDateString
) {

    const birth =
        parseDateInput(
            birthDateString
        );


    const target =
        parseDateInput(
            targetDateString
        );


    let age =
        target.getFullYear()
        -
        birth.getFullYear();


    const monthDifference =
        target.getMonth()
        -
        birth.getMonth();


    if (
        monthDifference < 0
        ||
        (
            monthDifference === 0
            &&
            target.getDate()
            <
            birth.getDate()
        )
    ) {

        age--;

    }


    return age;

}


// ==========================================================
// FORMAT AGE
// ==========================================================

function formatAge(
    decimalAge
) {

    let years =
        Math.floor(
            decimalAge
        );


    let months =
        Math.round(
            (
                decimalAge
                -
                years
            )
            *
            12
        );


    if (
        months === 12
    ) {

        years +=
            1;

        months =
            0;

    }


    if (
        months === 0
    ) {

        return `Age ${years}`;

    }


    return `Age ${years}y ${months}m`;

}


// ==========================================================
// CURRENCY FORMATTER
// ==========================================================

function formatCurrency(
    value
) {

    const numericValue =
        Number(
            value
        );


    if (
        !Number.isFinite(
            numericValue
        )
    ) {

        return "N/A";

    }


    const formatted =
        new Intl.NumberFormat(
            "en-GH",
            {
                minimumFractionDigits:
                    2,

                maximumFractionDigits:
                    2
            }
        )
        .format(
            numericValue
        );


    return `GH¢${formatted}`;

}


// ==========================================================
// TEXT FORMATTER
// ==========================================================

function formatText(
    value
) {

    if (
        value === null
        ||
        value === undefined
        ||
        value === ""
    ) {

        return "-";

    }


    return String(
        value
    )
    .replaceAll(
        "_",
        " "
    )
    .replaceAll(
        "-",
        " "
    )
    .toLowerCase()
    .replace(
        /\b\w/g,
        character =>
            character
            .toUpperCase()
    );

}


// ==========================================================
// API ERROR HANDLING
// ==========================================================

function extractApiError(
    data,
    fallbackMessage
) {

    if (!data) {

        return fallbackMessage;

    }


    if (
        typeof data.detail
        ===
        "string"
    ) {

        return data.detail;

    }


    if (
        Array.isArray(
            data.detail
        )
    ) {

        return data.detail
            .map(
                item => {

                    if (
                        item.msg
                    ) {

                        return item.msg;

                    }

                    return JSON.stringify(
                        item
                    );

                }
            )
            .join(
                " "
            );

    }


    if (
        data.message
    ) {

        return data.message;

    }


    return fallbackMessage;

}


// ==========================================================
// ERROR DISPLAY
// ==========================================================

function showError(
    message
) {

    errorMessage.textContent =
        message;


    errorMessage.classList.remove(
        "hidden"
    );


    errorMessage.scrollIntoView(
        {
            behavior: "smooth",
            block: "center"
        }
    );

}


function hideError() {

    errorMessage.classList.add(
        "hidden"
    );


    errorMessage.textContent =
        "";

}


// ==========================================================
// LOADING STATES
// ==========================================================

function setPensionLoading(
    isLoading
) {

    calculateButton.disabled =
        isLoading;


    buttonText.textContent =
        isLoading
        ?
        "Calculating..."
        :
        "Calculate My Pension";

}


function setComparisonLoading(
    isLoading
) {

    compareButton.disabled =
        isLoading;


    compareButton.textContent =
        isLoading
        ?
        "Running Actuarial Analysis..."
        :
        "Compare Retirement Ages";


    const loadingState =
        document.getElementById(
            "comparison-loading-state"
        );


    if (loadingState) {

        loadingState.classList.toggle(
            "hidden",
            !isLoading
        );

    }


    if (isLoading) {

        comparisonResults.classList.add(
            "hidden"
        );

    }

}


// ==========================================================
// STAGE 3 — VISUAL ACTUARIAL ANALYSIS HELPERS
// ==========================================================

function updateComparisonInsightCard(
    cardId,
    valueText,
    detailText,
    tone = "neutral"
) {

    const card =
        document.getElementById(
            cardId
        );


    if (!card) {
        return;
    }


    card.classList.remove(
        "is-positive",
        "is-neutral",
        "is-caution"
    );


    card.classList.add(
        `is-${tone}`
    );


    const value =
        card.querySelector(
            "strong"
        );

    const detail =
        card.querySelector(
            "small"
        );


    if (value) {
        value.textContent =
            valueText;
    }


    if (detail) {
        detail.textContent =
            detailText;
    }

}


function appendComparisonMetricTag(
    parent,
    label
) {

    if (!parent) {
        return;
    }


    const existing =
        parent.querySelector(
            ".metric-highlight-tag"
        );


    if (existing) {
        return;
    }


    const tag =
        document.createElement(
            "span"
        );

    tag.className =
        "metric-highlight-tag";

    tag.textContent =
        label;


    parent.appendChild(
        tag
    );

}


function animateComparisonBar(
    bar
) {

    if (!bar) {
        return;
    }


    const targetWidth =
        bar.style.width;


    if (!targetWidth) {
        return;
    }


    bar.style.width =
        "0%";


    requestAnimationFrame(
        () => {
            bar.style.width =
                targetWidth;
        }
    );

}


function decorateOrdinaryComparisonInsights(
    scenarios,
    annualDiscountRate,
    projectionAge
) {

    const validScenarios =
        Array.isArray(scenarios)
        ?
        scenarios
        :
        [];


    const monthlyValues =
        validScenarios.map(
            scenario =>
                Number(
                    scenario.monthly_benefit
                    ||
                    0
                )
        );


    const highestMonthly =
        monthlyValues.length
        ?
        Math.max(
            ...monthlyValues
        )
        :
        0;


    const highestMonthlyIndex =
        highestMonthly > 0
        ?
        monthlyValues.findIndex(
            value =>
                Math.abs(
                    value
                    -
                    highestMonthly
                )
                <
                0.01
        )
        :
        -1;


    if (highestMonthlyIndex >= 0) {

        const highestScenario =
            validScenarios[
                highestMonthlyIndex
            ];


        updateComparisonInsightCard(
            "monthly-pension-insight",
            `Age ${highestScenario.retirement_age}`,
            `${formatCurrency(highestMonthly)} per month is the highest estimated monthly pension in this comparison.`,
            "positive"
        );

    }
    else {

        updateComparisonInsightCard(
            "monthly-pension-insight",
            "No monthly pension",
            "No eligible monthly pension scenario was available in this comparison.",
            "neutral"
        );

    }


    const retirementRows =
        document.querySelectorAll(
            "#retirement-chart .chart-row"
        );


    retirementRows.forEach(
        (row, index) => {

            const scenario =
                validScenarios[index];

            const bar =
                row.querySelector(
                    ".chart-bar"
                );


            animateComparisonBar(
                bar
            );


            if (!scenario) {
                return;
            }


            const amount =
                Number(
                    scenario.monthly_benefit
                    ||
                    0
                );


            row.title =
                amount > 0
                ?
                `Age ${scenario.retirement_age}: ${formatCurrency(amount)} estimated monthly pension`
                :
                `Age ${scenario.retirement_age}: no monthly pension available`;


            if (index === highestMonthlyIndex) {

                row.classList.add(
                    "is-best-metric"
                );


                appendComparisonMetricTag(
                    row.querySelector(
                        ".chart-age"
                    ),
                    "Highest"
                );

            }

        }
    );


    const comparisonRows =
        document.querySelectorAll(
            "#comparison-body tr"
        );


    if (
        highestMonthlyIndex >= 0
        &&
        comparisonRows[
            highestMonthlyIndex
        ]
    ) {

        comparisonRows[
            highestMonthlyIndex
        ].classList.add(
            "metric-winner-row"
        );

    }


    const age55Scenario =
        validScenarios.find(
            scenario =>
                Number(
                    scenario.retirement_age
                )
                ===
                55
        );

    const age60Scenario =
        validScenarios.find(
            scenario =>
                Number(
                    scenario.retirement_age
                )
                ===
                60
        );


    if (
        age55Scenario
        &&
        age60Scenario
    ) {

        const breakEvenAge =
            calculateBreakEvenAge(
                55,
                Number(
                    age55Scenario.monthly_benefit
                    ||
                    0
                ),
                Number(
                    age60Scenario.monthly_benefit
                    ||
                    0
                )
            );


        updateComparisonInsightCard(
            "breakeven-insight",
            breakEvenAge === null
            ?
            "No crossover"
            :
            formatAge(
                breakEvenAge
            ),
            breakEvenAge === null
            ?
            "For age 55 versus age 60, no cumulative undiscounted cash-flow crossover occurs before age 100 in this model."
            :
            `For age 55 versus age 60, the age-60 strategy catches up around ${formatAge(breakEvenAge)} in cumulative undiscounted pension payments.`,
            "neutral"
        );


        const benchmarkCard =
            document.querySelector(
                "#breakeven-results .breakeven-item"
            );


        if (benchmarkCard) {

            benchmarkCard.classList.add(
                "is-benchmark"
            );


            appendComparisonMetricTag(
                benchmarkCard,
                "Benchmark"
            );

        }

    }
    else {

        updateComparisonInsightCard(
            "breakeven-insight",
            "Unavailable",
            "Age 55 and age 60 pension data are required for the crossover benchmark.",
            "neutral"
        );

    }


    const monthlyRate =
        Math.pow(
            1
            +
            annualDiscountRate,
            1 / 12
        )
        -
        1;


    const presentValues =
        validScenarios.map(
            scenario =>
                calculatePensionPresentValue(
                    scenario.retirement_age,
                    Number(
                        scenario.monthly_benefit
                        ||
                        0
                    ),
                    projectionAge,
                    monthlyRate
                )
        );


    const highestPV =
        presentValues.length
        ?
        Math.max(
            ...presentValues
        )
        :
        0;


    const highestPVIndex =
        highestPV > 0
        ?
        presentValues.findIndex(
            value =>
                Math.abs(
                    value
                    -
                    highestPV
                )
                <
                0.01
        )
        :
        -1;


    if (highestPVIndex >= 0) {

        const highestScenario =
            validScenarios[
                highestPVIndex
            ];


        updateComparisonInsightCard(
            "pv-insight",
            `Age ${highestScenario.retirement_age}`,
            `${formatCurrency(highestPV)} is the highest discounted present value measured at age 55 under the selected assumptions.`,
            "positive"
        );


        const pvCards =
            document.querySelectorAll(
                "#pv-results .pv-item"
            );


        const winningCard =
            pvCards[
                highestPVIndex
            ];


        if (winningCard) {

            winningCard.classList.add(
                "is-best-metric"
            );


            appendComparisonMetricTag(
                winningCard,
                "Highest PV"
            );

        }

    }
    else {

        updateComparisonInsightCard(
            "pv-insight",
            "No PV available",
            "No positive discounted pension value was available under the selected assumptions.",
            "neutral"
        );

    }

}


function decorateEPVComparisonInsights(
    scenarios
) {

    const validScenarios =
        Array.isArray(scenarios)
        ?
        scenarios
        :
        [];


    const epvValues =
        validScenarios.map(
            scenario =>
                Number(
                    scenario.expected_present_value
                    ||
                    0
                )
        );


    const highestEPV =
        epvValues.length
        ?
        Math.max(
            ...epvValues
        )
        :
        0;


    const highestEPVIndex =
        highestEPV > 0
        ?
        epvValues.findIndex(
            value =>
                Math.abs(
                    value
                    -
                    highestEPV
                )
                <
                0.01
        )
        :
        -1;


    if (highestEPVIndex >= 0) {

        const highestScenario =
            validScenarios[
                highestEPVIndex
            ];


        updateComparisonInsightCard(
            "epv-insight",
            `Age ${highestScenario.retirement_age}`,
            `${formatCurrency(highestEPV)} is the highest mortality-adjusted EPV under the selected assumptions.`,
            "positive"
        );

    }
    else {

        updateComparisonInsightCard(
            "epv-insight",
            "No EPV available",
            "No eligible monthly pension scenario was available for mortality-adjusted comparison.",
            "neutral"
        );

    }


    const epvRows =
        document.querySelectorAll(
            "#epv-chart .epv-chart-row"
        );


    epvRows.forEach(
        (row, index) => {

            const scenario =
                validScenarios[index];

            const bar =
                row.querySelector(
                    ".epv-chart-bar"
                );


            animateComparisonBar(
                bar
            );


            if (!scenario) {
                return;
            }


            const epv =
                Number(
                    scenario.expected_present_value
                    ||
                    0
                );


            row.title =
                epv > 0
                ?
                `Age ${scenario.retirement_age}: ${formatCurrency(epv)} mortality-adjusted EPV`
                :
                `Age ${scenario.retirement_age}: no EPV available`;


            if (index === highestEPVIndex) {

                row.classList.add(
                    "is-best-metric"
                );


                appendComparisonMetricTag(
                    row.querySelector(
                        ".epv-chart-age"
                    ),
                    "Highest"
                );

            }

        }
    );


    const epvTableRows =
        document.querySelectorAll(
            "#epv-table-body tr"
        );


    if (
        highestEPVIndex >= 0
        &&
        epvTableRows[
            highestEPVIndex
        ]
    ) {

        epvTableRows[
            highestEPVIndex
        ].classList.add(
            "metric-winner-row"
        );

    }

}
