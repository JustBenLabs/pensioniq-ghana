// ==========================================================
// PENSIONIQ GHANA
// FINAL FRONTEND APPLICATION LOGIC
// ==========================================================


// ==========================================================
// API CONFIGURATION
// ==========================================================

const API_BASE_URL =
    window.location.hostname === "127.0.0.1"
    ||
    window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://pensioniq-ghana.onrender.com";


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
                contributionMonths
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
    contributionMonths
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


    tableBody.innerHTML =
        "";


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


            const status =
                scenario.retirement_age === 60
                ?
                `
                <span class="recommended-tag">
                    Full Pension Age
                </span>
                `
                :
                formatText(
                    scenario.benefit_type
                );


            row.innerHTML = `

                <td>
                    ${scenario.retirement_age}
                </td>

                <td>
                    ${Number(
                        scenario.contribution_months
                    ).toLocaleString()}
                </td>

                <td>
                    ${pensionRight}
                </td>

                <td>
                    ${pension}
                </td>

                <td>
                    ${status}
                </td>

            `;


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


    chart.innerHTML =
        "";


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


            row.innerHTML = `

                <div class="chart-age">
                    Age ${scenario.retirement_age}
                </div>

                <div class="chart-track">

                    <div
                        class="chart-bar"
                        style="width: ${width}%"
                    >
                    </div>

                </div>

                <div class="chart-amount">

                    ${
                        pension > 0
                        ?
                        formatCurrency(
                            pension
                        )
                        :
                        "N/A"
                    }

                </div>

            `;


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


    container.innerHTML =
        "";


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

        container.innerHTML =
            "<p>Age 60 pension data is unavailable.</p>";

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


                card.innerHTML = `

                    <span>
                        Retire at Age
                        ${scenario.retirement_age}
                    </span>

                    <strong>
                        ${resultText}
                    </strong>

                    <small>
                        ${explanation}
                    </small>

                `;


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


    container.innerHTML =
        "";


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


            card.innerHTML = `

                <span>
                    Retire at Age
                    ${scenario.retirement_age}
                </span>

                <strong>

                    ${
                        scenario.presentValue > 0
                        ?
                        formatCurrency(
                            scenario.presentValue
                        )
                        :
                        "N/A"
                    }

                </strong>

                <small>

                    ${
                        isHighest
                        ?
                        "Highest present value under these assumptions"
                        :
                        "Value measured at age 55"
                    }

                </small>

            `;


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


    tableBody.innerHTML =
        "";


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


            row.innerHTML = `

                <td>
                    ${scenario.retirement_age}
                </td>

                <td>
                    ${monthlyPension}
                </td>

                <td>
                    ${pensionRight}
                </td>

                <td>
                    ${epv}
                </td>

            `;


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


    chart.innerHTML =
        "";


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


            row.innerHTML = `

                <div class="epv-chart-age">
                    Age ${scenario.retirement_age}
                </div>

                <div class="epv-chart-track">

                    <div
                        class="epv-chart-bar"
                        style="width: ${width}%"
                    >
                    </div>

                </div>

                <div class="epv-chart-value">

                    ${
                        epv > 0
                        ?
                        formatCurrency(
                            epv
                        )
                        :
                        "N/A"
                    }

                </div>

            `;


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

        summary.innerHTML = `

            <span>
                Mortality-adjusted actuarial analysis
            </span>

            <strong>
                No EPV available
            </strong>

            <p>
                No eligible monthly pension scenario
                was available for this comparison.
            </p>

        `;

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


    summary.innerHTML = `

        <span>
            Highest mortality-adjusted EPV
            under these assumptions
        </span>

        <strong>
            ${formatCurrency(
                highest.expected_present_value
            )}
        </strong>

        <p>
            Retirement age ${highest.retirement_age}.
            This result depends on the selected mortality,
            discount-rate and projection assumptions and
            should not be interpreted as a universal
            recommendation.
        </p>

    `;

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

}