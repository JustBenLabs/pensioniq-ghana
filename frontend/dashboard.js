// ==========================================================
// PENSIONIQ GHANA
// AUTHENTICATED MEMBER DASHBOARD
// ==========================================================


// ==========================================================
// CONFIGURATION
// ==========================================================

const API_BASE_URL =
    window.PENSIONIQ_API_BASE_URL;


const ACCESS_TOKEN_KEY =
    "pensioniq_access_token";


// ==========================================================
// APPLICATION STATE
// ==========================================================

let currentMemberId = null;

let currentEditingContributionId = null;

let contributionRecords = [];

let currentMemberData = null;


// ==========================================================
// DOM ELEMENTS
// ==========================================================

const dashboard =
    document.getElementById(
        "dashboard"
    );


const dashboardLoading =
    document.getElementById(
        "dashboard-loading"
    );


const errorBox =
    document.getElementById(
        "dashboard-error"
    );


const logoutButton =
    document.getElementById(
        "logout-button"
    );


const contributionForm =
    document.getElementById(
        "contribution-form"
    );


const addContributionButton =
    document.getElementById(
        "add-contribution-button"
    );


const cancelEditButton =
    document.getElementById(
        "cancel-edit-button"
    );


const contributionSuccess =
    document.getElementById(
        "contribution-success"
    );

const editProfileButton =
    document.getElementById(
        "edit-profile-button"
    );


const profileDisplay =
    document.getElementById(
        "profile-display"
    );


const profileForm =
    document.getElementById(
        "profile-form"
    );


const saveProfileButton =
    document.getElementById(
        "save-profile-button"
    );


const cancelProfileButton =
    document.getElementById(
        "cancel-profile-button"
    );


const profileSuccess =
    document.getElementById(
        "profile-success"
    );

const openPasswordFormButton =
    document.getElementById(
        "open-password-form-button"
    );


const passwordForm =
    document.getElementById(
        "password-form"
    );


const savePasswordButton =
    document.getElementById(
        "save-password-button"
    );


const cancelPasswordButton =
    document.getElementById(
        "cancel-password-button"
    );


const passwordSuccess =
    document.getElementById(
        "password-success"
    );    
// ==========================================================
// EVENT LISTENERS
// ==========================================================


// ----------------------------------------------------------
// Authentication
// ----------------------------------------------------------

logoutButton.addEventListener(
    "click",
    logout
);


// ----------------------------------------------------------
// Contributions
// ----------------------------------------------------------

contributionForm.addEventListener(
    "submit",
    saveContribution
);


cancelEditButton.addEventListener(
    "click",
    cancelContributionEdit
);


// ----------------------------------------------------------
// Profile Management
// ----------------------------------------------------------

editProfileButton.addEventListener(
    "click",
    startProfileEdit
);


cancelProfileButton.addEventListener(
    "click",
    cancelProfileEdit
);


profileForm.addEventListener(
    "submit",
    saveProfile
);


// ----------------------------------------------------------
// Password / Account Security
// ----------------------------------------------------------

openPasswordFormButton.addEventListener(
    "click",
    openPasswordForm
);


cancelPasswordButton.addEventListener(
    "click",
    closePasswordForm
);


passwordForm.addEventListener(
    "submit",
    changePassword
);
// ==========================================================
// PASSWORD FORM
// ==========================================================

function openPasswordForm() {

    hideError();

    hidePasswordSuccess();


    passwordForm.classList.remove(
        "hidden"
    );


    openPasswordFormButton.classList.add(
        "hidden"
    );


    document.getElementById(
        "current-password"
    ).focus();

}


function closePasswordForm() {

    passwordForm.reset();


    passwordForm.classList.add(
        "hidden"
    );


    openPasswordFormButton.classList.remove(
        "hidden"
    );


    hidePasswordSuccess();

}


// ==========================================================
// CHANGE PASSWORD
// ==========================================================

async function changePassword(
    event
) {

    event.preventDefault();


    hideError();

    hidePasswordSuccess();


    const currentPassword =
        document.getElementById(
            "current-password"
        ).value;


    const newPassword =
        document.getElementById(
            "new-password"
        ).value;


    const confirmPassword =
        document.getElementById(
            "confirm-new-password"
        ).value;


    if (!currentPassword) {

        showError(
            "Please enter your current password."
        );

        return;

    }


    if (newPassword.length < 8) {

        showError(
            "Your new password must contain at least 8 characters."
        );

        return;

    }


    if (
        newPassword !==
        confirmPassword
    ) {

        showError(
            "The new passwords do not match."
        );

        return;

    }


    if (
        newPassword ===
        currentPassword
    ) {

        showError(
            "Your new password must be different from your current password."
        );

        return;

    }


    setPasswordLoading(
        true
    );


    try {

        const response =
            await authenticatedFetch(
                `${API_BASE_URL}/auth/change-password`,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {

                                current_password:
                                    currentPassword,

                                new_password:
                                    newPassword

                            }
                        )

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    "Unable to change your password."
                )
            );

        }


        passwordForm.reset();


        showPasswordSuccess(
            "Password changed successfully. Redirecting you to sign in..."
        );


        // Clear the browser's current token.
        sessionStorage.removeItem(
            ACCESS_TOKEN_KEY
        );


        setTimeout(
            () => {

                window.location.href =
                    "login.html";

            },
            1500
        );

    }

    catch (error) {

        showError(
            error.message
        );

    }

    finally {

        setPasswordLoading(
            false
        );

    }

}


// ==========================================================
// PASSWORD LOADING
// ==========================================================

function setPasswordLoading(
    loading
) {

    savePasswordButton.disabled =
        loading;


    cancelPasswordButton.disabled =
        loading;


    savePasswordButton.textContent =
        loading
        ?
        "Changing Password..."
        :
        "Change Password";

}


// ==========================================================
// PASSWORD SUCCESS
// ==========================================================

function showPasswordSuccess(
    message
) {

    passwordSuccess.textContent =
        message;


    passwordSuccess.classList.remove(
        "hidden"
    );

}


function hidePasswordSuccess() {

    passwordSuccess.textContent =
        "";


    passwordSuccess.classList.add(
        "hidden"
    );

}
// ==========================================================
// AUTHENTICATION
// ==========================================================

function getAccessToken() {

    return sessionStorage.getItem(
        ACCESS_TOKEN_KEY
    );

}


async function logout() {

    const token =
        getAccessToken();


    try {

        if (token) {

            await fetch(
                `${API_BASE_URL}/auth/logout`,
                {
                    method: "POST",

                    headers: {
                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );

        }

    }
    catch (error) {

        console.error(
            "Server logout failed:",
            error
        );

    }
    finally {

        // Always remove the local token,
        // even if the network request fails.

        sessionStorage.removeItem(
            ACCESS_TOKEN_KEY
        );


        currentMemberId =
            null;


        window.location.href =
            "login.html";

    }

}

function redirectToLogin() {

    window.location.href =
        "login.html";

}


// ==========================================================
// AUTHENTICATED FETCH
// ==========================================================

async function authenticatedFetch(
    url,
    options = {}
) {

    const token =
        getAccessToken();


    if (!token) {

        redirectToLogin();

        throw new Error(
            "Authentication required."
        );

    }


    const headers = {

        ...(options.headers || {}),

        Authorization:
            `Bearer ${token}`

    };


    const response =
        await fetch(
            url,
            {
                ...options,
                headers: headers
            }
        );


    if (
        response.status === 401
    ) {

        sessionStorage.removeItem(
            ACCESS_TOKEN_KEY
        );


        window.location.href =
            "login.html";


        throw new Error(
            "Your session has expired. Please sign in again."
        );

    }


    return response;

}


// ==========================================================
// INITIALISE DASHBOARD
// ==========================================================

async function initialiseDashboard() {

    hideError();

    hideContributionSuccess();


    const token =
        getAccessToken();


    if (!token) {

        redirectToLogin();

        return;

    }


    try {

        // --------------------------------------------------
        // Identify authenticated user
        // --------------------------------------------------

        const authResponse =
            await authenticatedFetch(
                `${API_BASE_URL}/auth/me`
            );


        const authData =
            await authResponse.json();


        if (!authResponse.ok) {

            throw new Error(
                getApiErrorMessage(
                    authData,
                    "Unable to verify your account."
                )
            );

        }


        if (
            !authData.member
            ||
            !authData.member.id
        ) {

            throw new Error(
                "No member profile is linked to this account."
            );

        }


        currentMemberId =
            Number(
                authData.member.id
            );


        // --------------------------------------------------
        // Load full dashboard
        // --------------------------------------------------

        await refreshCurrentDashboard();


        dashboardLoading.classList.add(
            "hidden"
        );


        dashboard.classList.remove(
            "hidden"
        );

    }

    catch (error) {

        dashboardLoading.classList.add(
            "hidden"
        );


        if (
            window.location.pathname
            .endsWith(
                "login.html"
            )
        ) {

            return;

        }


        showError(
            error.message
        );

    }

}


// ==========================================================
// REFRESH DASHBOARD
// ==========================================================

async function refreshCurrentDashboard() {

    if (!currentMemberId) {

        return;

    }


    const response =
        await authenticatedFetch(
            `${API_BASE_URL}/members/${currentMemberId}/dashboard`
        );


    const data =
        await response.json();


    if (!response.ok) {

        throw new Error(
            getApiErrorMessage(
                data,
                "Unable to load dashboard."
            )
        );

    }


    displayDashboard(
        data
    );


    await loadContributionHistory();

}


// ==========================================================
// DISPLAY DASHBOARD
// ==========================================================

function displayDashboard(
    data
) {

    displayMember(
        data.member
    );


    displayPensionPosition(
        data.pension_position
    );


    displayContributionSummary(
        data.contribution_summary
    );


    displayContributionHealth(
        data.contribution_health
    );

}


// ==========================================================
// MEMBER INFORMATION
// ==========================================================

function displayMember(
    member
) {

    currentMemberData =
        member;


    document.getElementById(
        "member-name"
    ).textContent =
        member.full_name;


    document.getElementById(
        "member-summary"
    ).textContent =
        `${member.sex} · Age ${member.current_age}`;


    document.getElementById(
        "member-initials"
    ).textContent =
        getInitials(
            member.first_name,
            member.last_name
        );


    document.getElementById(
        "profile-first-name"
    ).textContent =
        member.first_name;


    document.getElementById(
        "profile-last-name"
    ).textContent =
        member.last_name;


    document.getElementById(
        "profile-dob"
    ).textContent =
        formatDate(
            member.date_of_birth
        );


    document.getElementById(
        "profile-age"
    ).textContent =
        `${member.current_age} years`;


    document.getElementById(
        "profile-sex"
    ).textContent =
        member.sex;


    document.getElementById(
        "profile-salary"
    ).textContent =
        formatCurrency(
            member
            .best_three_year_average_annual_salary
        );

}

// ==========================================================
// PENSION POSITION
// ==========================================================

function displayPensionPosition(
    position
) {

    document.getElementById(
        "metric-months"
    ).textContent =
        Number(
            position.contribution_months
        ).toLocaleString();


    document.getElementById(
        "metric-years"
    ).textContent =
        `${position.contribution_years} contribution years`;


    document.getElementById(
        "metric-pension-right"
    ).textContent =
        (
            position.pension_right_percent
            !== null
            &&
            position.pension_right_percent
            !== undefined
        )
        ?
        `${position.pension_right_percent}%`
        :
        "Not Yet Eligible";


    document.getElementById(
        "position-months"
    ).textContent =
        `${Number(
            position.contribution_months
        ).toLocaleString()} months`;


    document.getElementById(
        "position-right"
    ).textContent =
        (
            position.pension_right_percent
            !== null
            &&
            position.pension_right_percent
            !== undefined
        )
        ?
        `${position.pension_right_percent}%`
        :
        "—";


    document.getElementById(
        "months-to-minimum"
    ).textContent =
        Number(
            position.months_to_minimum
        ).toLocaleString();


    document.getElementById(
        "months-to-maximum"
    ).textContent =
        Number(
            position.months_to_maximum
        ).toLocaleString();


    document.getElementById(
        "maximum-right-reached"
    ).textContent =
        position.maximum_pension_right_reached
        ?
        "Yes"
        :
        "No";
    document.getElementById(
    "profile-contribution-months"
).textContent =
    Number(
        position.contribution_months
    ).toLocaleString();    


    // ------------------------------------------------------
    // Eligibility badge
    // ------------------------------------------------------

    const badge =
        document.getElementById(
            "eligibility-badge"
        );


    if (
        position
        .eligible_for_monthly_old_age_pension
    ) {

        badge.textContent =
            "Monthly Pension Threshold Reached";


        badge.className =
            "status-badge status-success";

    }

    else {

        badge.textContent =
            "Below Minimum";


        badge.className =
            "status-badge status-warning";

    }


    // ------------------------------------------------------
    // Progress
    // ------------------------------------------------------

    const months =
        Number(
            position.contribution_months
        );


    const minimum =
        Number(
            position.minimum_months_required
            ||
            180
        );


    const maximum =
        Number(
            position.maximum_pension_right_months
            ||
            420
        );


    let progress =
        0;


    if (
        months >= minimum
    ) {

        progress =
            (
                (
                    months
                    -
                    minimum
                )
                /
                (
                    maximum
                    -
                    minimum
                )
            )
            *
            100;

    }


    progress =
        Math.min(
            Math.max(
                progress,
                0
            ),
            100
        );


    document.getElementById(
        "pension-progress-bar"
    ).style.width =
        `${progress}%`;


    // ------------------------------------------------------
    // Message
    // ------------------------------------------------------

    const message =
        document.getElementById(
            "position-message"
        );


    if (
        months < minimum
    ) {

        message.textContent =
            `${position.months_to_minimum} months remain to the minimum monthly-pension threshold`;

    }

    else if (
        months < maximum
    ) {

        message.textContent =
            `${position.months_to_maximum} months remain to the maximum pension-right threshold`;

    }

    else {

        message.textContent =
            "Maximum pension-right threshold reached";

    }

}


// ==========================================================
// CONTRIBUTION SUMMARY
// ==========================================================

function displayContributionSummary(
    summary
) {

    document.getElementById(
        "detailed-records"
    ).textContent =
        Number(
            summary.detailed_records_stored
        ).toLocaleString();


    document.getElementById(
        "continuity-ratio"
    ).textContent =
        (
            summary.continuity_ratio_percent
            !== null
            &&
            summary.continuity_ratio_percent
            !== undefined
        )
        ?
        `${summary.continuity_ratio_percent}%`
        :
        "No Data";


    document.getElementById(
        "missing-count"
    ).textContent =
        Number(
            summary.missing_month_count
        ).toLocaleString();


    document.getElementById(
        "mismatch-count"
    ).textContent =
        Number(
            summary.amount_mismatch_count
        ).toLocaleString();


    document.getElementById(
        "total-earnings"
    ).textContent =
        formatCurrency(
            summary.total_insurable_earnings
        );


    document.getElementById(
        "total-first-tier"
    ).textContent =
        formatCurrency(
            summary.total_recorded_first_tier
        );


    document.getElementById(
        "metric-missing"
    ).textContent =
        Number(
            summary.missing_month_count
        ).toLocaleString();


    document.getElementById(
        "record-alignment"
    ).textContent =
        formatStatus(
            summary.record_alignment_status
        );


    const description =
        document.getElementById(
            "alignment-description"
        );


    if (
        summary.record_alignment_status
        ===
        "ALIGNED"
    ) {

        description.textContent =
            "The stored contribution total matches the number of detailed monthly records.";

    }

    else if (
        summary.record_alignment_status
        ===
        "NO_DETAILED_HISTORY"
    ) {

        description.textContent =
            "No month-by-month contribution history has been added to PensionIQ yet.";

    }

    else if (
        summary.record_alignment_status
        ===
        "TOTAL_AND_HISTORY_DIFFER"
    ) {

        description.textContent =
            "The stored contribution-month total differs from the detailed records currently stored in PensionIQ.";

    }

    else {

        description.textContent =
            "Contribution record alignment information is unavailable.";

    }


    displayHealthStatus(
        summary.health_status,
        summary.continuity_ratio_percent
    );

}


// ==========================================================
// HEALTH STATUS
// ==========================================================

function displayHealthStatus(
    status,
    continuityRatio
) {

    const badge =
        document.getElementById(
            "health-status-badge"
        );


    const metric =
        document.getElementById(
            "metric-health"
        );


    const description =
        document.getElementById(
            "metric-health-description"
        );


    if (
        status ===
        "RECORDED_HISTORY_COMPLETE"
    ) {

        badge.textContent =
            "Healthy";


        badge.className =
            "status-badge status-success";


        metric.textContent =
            (
                continuityRatio
                !== null
                &&
                continuityRatio
                !== undefined
            )
            ?
            `${continuityRatio}%`
            :
            "Healthy";


        description.textContent =
            "No missing months detected in the observed contribution period";

    }

    else if (
        status ===
        "INCOMPLETE_RECORDED_HISTORY"
    ) {

        badge.textContent =
            "Missing Records";


        badge.className =
            "status-badge status-warning";


        metric.textContent =
            (
                continuityRatio
                !== null
                &&
                continuityRatio
                !== undefined
            )
            ?
            `${continuityRatio}%`
            :
            "Review";


        description.textContent =
            "One or more months are missing from the stored contribution history";

    }

    else if (
        status ===
        "AMOUNT_REVIEW_NEEDED"
    ) {

        badge.textContent =
            "Amount Review";


        badge.className =
            "status-badge status-warning";


        metric.textContent =
            "Review";


        description.textContent =
            "One or more recorded contribution amounts require review";

    }

    else if (
        status ===
        "NO_DATA"
    ) {

        badge.textContent =
            "No Detailed Data";


        badge.className =
            "status-badge";


        metric.textContent =
            "No Data";


        description.textContent =
            "No month-by-month contribution records are stored yet";

    }

    else {

        badge.textContent =
            formatStatus(
                status
            );


        badge.className =
            "status-badge status-warning";


        metric.textContent =
            "Review";


        description.textContent =
            "Contribution records require review";

    }

}


// ==========================================================
// CONTRIBUTION HEALTH
// ==========================================================

function displayContributionHealth(
    health
) {

    displayMissingMonths(
        health.missing_months
        ||
        []
    );


    displayAmountChecks(
        health.amount_checks
        ||
        []
    );

}


// ==========================================================
// MISSING MONTHS
// ==========================================================

function displayMissingMonths(
    missingMonths
) {

    const container =
        document.getElementById(
            "missing-months-list"
        );


    container.innerHTML =
        "";


    if (
        missingMonths.length === 0
    ) {

        const chip =
            document.createElement(
                "span"
            );


        chip.className =
            "month-chip no-gap-chip";


        chip.textContent =
            "No missing months detected";


        container.appendChild(
            chip
        );


        return;

    }


    missingMonths.forEach(
        item => {

            const chip =
                document.createElement(
                    "span"
                );


            chip.className =
                "month-chip";


            chip.textContent =
                `${item.month_name} ${item.year}`;


            container.appendChild(
                chip
            );

        }
    );

}


// ==========================================================
// AMOUNT CHECKS
// ==========================================================

function displayAmountChecks(
    checks
) {

    const body =
        document.getElementById(
            "amount-check-body"
        );


    const emptyState =
        document.getElementById(
            "no-contribution-data"
        );


    body.innerHTML =
        "";


    if (
        checks.length === 0
    ) {

        emptyState.classList.remove(
            "hidden"
        );


        return;

    }


    emptyState.classList.add(
        "hidden"
    );


    checks.forEach(
        check => {

            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>
                    ${check.month_name} ${check.year}
                </td>

                <td>
                    ${formatCurrency(
                        check.insurable_earnings
                    )}
                </td>

                <td>
                    ${
                        check.recorded_first_tier
                        !== null
                        ?
                        formatCurrency(
                            check.recorded_first_tier
                        )
                        :
                        "—"
                    }
                </td>

                <td>
                    ${
                        check.expected_first_tier
                        !== null
                        ?
                        formatCurrency(
                            check.expected_first_tier
                        )
                        :
                        "—"
                    }
                </td>

                <td>
                    ${
                        check.difference
                        !== null
                        ?
                        formatCurrency(
                            check.difference
                        )
                        :
                        "—"
                    }
                </td>

                <td>
                    ${createCheckStatus(
                        check.status
                    )}
                </td>

            `;


            body.appendChild(
                row
            );

        }
    );

}


// ==========================================================
// LOAD CONTRIBUTION HISTORY
// ==========================================================

async function loadContributionHistory() {

    if (!currentMemberId) {

        return;

    }


    const response =
        await authenticatedFetch(
            `${API_BASE_URL}/members/${currentMemberId}/contributions`
        );


    const data =
        await response.json();


    if (!response.ok) {

        throw new Error(
            getApiErrorMessage(
                data,
                "Unable to load contribution history."
            )
        );

    }


    contributionRecords =
        data.contributions
        ||
        [];


    displayContributionHistory(
        contributionRecords
    );

}


// ==========================================================
// DISPLAY CONTRIBUTION HISTORY
// ==========================================================

function displayContributionHistory(
    records
) {

    const body =
        document.getElementById(
            "contribution-history-body"
        );


    const wrapper =
        document.getElementById(
            "contribution-history-wrapper"
        );


    const emptyState =
        document.getElementById(
            "contribution-history-empty"
        );


    body.innerHTML =
        "";


    if (
        records.length === 0
    ) {

        wrapper.classList.add(
            "hidden"
        );


        emptyState.classList.remove(
            "hidden"
        );


        return;

    }


    wrapper.classList.remove(
        "hidden"
    );


    emptyState.classList.add(
        "hidden"
    );


    records.forEach(
        record => {

            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>
                    ${getMonthName(record.month)}
                    ${record.year}
                </td>

                <td>
                    ${formatCurrency(
                        record.insurable_earnings
                    )}
                </td>

                <td>
                    ${
                        record
                        .recorded_first_tier_contribution
                        !== null
                        ?
                        formatCurrency(
                            record
                            .recorded_first_tier_contribution
                        )
                        :
                        "—"
                    }
                </td>

                <td>

                    <div class="table-actions">

                        <button
                            type="button"
                            class="action-button edit-button"
                            data-action="edit"
                            data-id="${record.id}"
                        >
                            Edit
                        </button>


                        <button
                            type="button"
                            class="action-button delete-button"
                            data-action="delete"
                            data-id="${record.id}"
                        >
                            Delete
                        </button>

                    </div>

                </td>

            `;


            body.appendChild(
                row
            );

        }
    );


    attachContributionActionHandlers();

}


// ==========================================================
// CONTRIBUTION ACTION HANDLERS
// ==========================================================

function attachContributionActionHandlers() {

    document
        .querySelectorAll(
            '[data-action="edit"]'
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        startContributionEdit(
                            Number(
                                button.dataset.id
                            )
                        );

                    }
                );

            }
        );


    document
        .querySelectorAll(
            '[data-action="delete"]'
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        deleteContribution(
                            Number(
                                button.dataset.id
                            )
                        );

                    }
                );

            }
        );

}


// ==========================================================
// ADD OR UPDATE CONTRIBUTION
// ==========================================================

async function saveContribution(
    event
) {

    event.preventDefault();


    hideError();

    hideContributionSuccess();


    if (!currentMemberId) {

        showError(
            "No authenticated member profile is available."
        );

        return;

    }


    const year =
        Number(
            document.getElementById(
                "contribution-year"
            ).value
        );


    const month =
        Number(
            document.getElementById(
                "contribution-month"
            ).value
        );


    const earnings =
        Number(
            document.getElementById(
                "contribution-earnings"
            ).value
        );


    const recordedInput =
        document.getElementById(
            "recorded-first-tier"
        ).value;


    const recordedContribution =
        recordedInput === ""
        ?
        null
        :
        Number(
            recordedInput
        );


    // ------------------------------------------------------
    // Validation
    // ------------------------------------------------------

    if (
        !Number.isInteger(year)
        ||
        year < 1900
        ||
        year > 2100
    ) {

        showError(
            "Please enter a valid contribution year."
        );

        return;

    }


    if (
        !Number.isInteger(month)
        ||
        month < 1
        ||
        month > 12
    ) {

        showError(
            "Please select a valid contribution month."
        );

        return;

    }
    const today =
    new Date();

const currentYear =
    today.getFullYear();

const currentMonth =
    today.getMonth() + 1;

if (
    year > currentYear
    ||
    (
        year === currentYear
        &&
        month > currentMonth
    )
) {
    showError(
        "Contribution period cannot be in the future."
    );

    return;
}

if (
    currentMemberData
    &&
    currentMemberData.date_of_birth
    &&
    !isContributionPeriodPlausibleForDob(
        currentMemberData.date_of_birth,
        year,
        month
    )
) {
    showError(
        "Contribution period is not plausible for your age."
    );

    return;
}


    if (
        !Number.isFinite(earnings)
        ||
        earnings < 0
    ) {

        showError(
            "Insurable earnings must be zero or greater."
        );

        return;

    }
    if (
    !hasAtMostTwoDecimalPlaces(
        earnings
    )
) {
    showError(
        "Insurable earnings cannot have more than 2 decimal places."
    );

    return;
}


    if (
        recordedContribution !== null
        &&
        (
            !Number.isFinite(
                recordedContribution
            )
            ||
            recordedContribution < 0
        )
    ) {

        showError(
            "Recorded First-Tier contribution cannot be negative."
        );

        return;

    }
    if (
    recordedContribution !== null
    &&
    !hasAtMostTwoDecimalPlaces(
        recordedContribution
    )
) {
    showError(
        "Recorded First-Tier contribution cannot have more than 2 decimal places."
    );

    return;
}


    const isEditing =
        currentEditingContributionId
        !==
        null;


    setContributionLoading(
        true
    );


    try {

        const url =
            isEditing
            ?
            `${API_BASE_URL}/members/${currentMemberId}/contributions/${currentEditingContributionId}`
            :
            `${API_BASE_URL}/members/${currentMemberId}/contributions`;


        const response =
            await authenticatedFetch(
                url,
                {

                    method:
                        isEditing
                        ?
                        "PUT"
                        :
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {

                                year:
                                    year,

                                month:
                                    month,

                                insurable_earnings:
                                    earnings,

                                recorded_first_tier_contribution:
                                    recordedContribution

                            }
                        )

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    isEditing
                    ?
                    "Unable to update contribution."
                    :
                    "Unable to add contribution."
                )
            );

        }


        const successMessage =
            isEditing
            ?
            `${getMonthName(month)} ${year} contribution updated successfully.`
            :
            `${getMonthName(month)} ${year} contribution added successfully.`;


        resetContributionForm();


        await refreshCurrentDashboard();


        showContributionSuccess(
            `${successMessage} Dashboard updated.`
        );

    }

    catch (error) {

        showError(
            error.message
        );

    }

    finally {

        setContributionLoading(
            false
        );

    }

}


// ==========================================================
// START EDIT
// ==========================================================

function startContributionEdit(
    contributionId
) {

    hideError();

    hideContributionSuccess();


    const record =
        contributionRecords.find(
            item =>
                Number(item.id)
                ===
                Number(contributionId)
        );


    if (!record) {

        showError(
            "Contribution record could not be found."
        );

        return;

    }


    currentEditingContributionId =
        Number(
            contributionId
        );


    document.getElementById(
        "contribution-year"
    ).value =
        record.year;


    document.getElementById(
        "contribution-month"
    ).value =
        record.month;


    document.getElementById(
        "contribution-earnings"
    ).value =
        record.insurable_earnings;


    document.getElementById(
        "recorded-first-tier"
    ).value =
        record
        .recorded_first_tier_contribution
        ??
        "";


    addContributionButton.textContent =
        "Save Changes";


    cancelEditButton.classList.remove(
        "hidden"
    );


    contributionForm.scrollIntoView(
        {
            behavior: "smooth",
            block: "center"
        }
    );

}


// ==========================================================
// CANCEL EDIT
// ==========================================================

function cancelContributionEdit() {

    resetContributionForm();

    hideContributionSuccess();

}


// ==========================================================
// RESET CONTRIBUTION FORM
// ==========================================================

function resetContributionForm() {

    currentEditingContributionId =
        null;


    contributionForm.reset();


    addContributionButton.textContent =
        "Add Contribution";


    cancelEditButton.classList.add(
        "hidden"
    );

}


// ==========================================================
// DELETE CONTRIBUTION
// ==========================================================

async function deleteContribution(
    contributionId
) {

    hideError();

    hideContributionSuccess();


    if (!currentMemberId) {

        showError(
            "No authenticated member profile is available."
        );

        return;

    }


    const record =
        contributionRecords.find(
            item =>
                Number(item.id)
                ===
                Number(contributionId)
        );


    if (!record) {

        showError(
            "Contribution record could not be found."
        );

        return;

    }


    const confirmed =
        window.confirm(
            `Delete the ${getMonthName(record.month)} ${record.year} contribution record?`
        );


    if (!confirmed) {

        return;

    }


    try {

        const response =
            await authenticatedFetch(
                `${API_BASE_URL}/members/${currentMemberId}/contributions/${contributionId}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    "Unable to delete contribution."
                )
            );

        }


        if (
            Number(
                currentEditingContributionId
            )
            ===
            Number(
                contributionId
            )
        ) {

            resetContributionForm();

        }


        await refreshCurrentDashboard();


        showContributionSuccess(
            `${getMonthName(record.month)} ${record.year} contribution deleted successfully.`
        );

    }

    catch (error) {

        showError(
            error.message
        );

    }

}


// ==========================================================
// CONTRIBUTION CHECK STATUS
// ==========================================================

function createCheckStatus(
    status
) {

    let className =
        "check-status";


    if (
        status ===
        "MATCHED"
    ) {

        className +=
            " check-matched";

    }

    else if (
        status ===
        "AMOUNT_MISMATCH"
    ) {

        className +=
            " check-danger";

    }

    else {

        className +=
            " check-warning";

    }


    return `

        <span class="${className}">
            ${formatStatus(status)}
        </span>

    `;

}


// ==========================================================
// API ERROR HANDLING
// ==========================================================

function getApiErrorMessage(
    data,
    fallback
) {

    if (!data) {

        return fallback;

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
                item =>
                    item.msg
                    ||
                    "Invalid information"
            )
            .join(" ");

    }


    if (
        typeof data.message
        ===
        "string"
    ) {

        return data.message;

    }


    return fallback;

}


// ==========================================================
// FORMAT CURRENCY
// ==========================================================

function formatCurrency(
    value
) {

    const amount =
        Number(
            value
        );


    if (
        !Number.isFinite(
            amount
        )
    ) {

        return "—";

    }


    const absolute =
        Math.abs(
            amount
        );


    const formatted =
        new Intl.NumberFormat(
            "en-GH",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )
        .format(
            absolute
        );


    return amount < 0
        ?
        `-GH¢${formatted}`
        :
        `GH¢${formatted}`;

}


// ==========================================================
// FORMAT STATUS
// ==========================================================

function formatStatus(
    value
) {

    if (!value) {

        return "—";

    }


    return String(value)
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
            letter =>
                letter.toUpperCase()
        );

}


// ==========================================================
// FORMAT DATE
// ==========================================================

function formatDate(
    value
) {

    if (!value) {

        return "—";

    }


    const [
        year,
        month,
        day
    ] =
        value
        .split("-")
        .map(Number);


    const date =
        new Date(
            year,
            month - 1,
            day
        );


    return new Intl.DateTimeFormat(
        "en-GB",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    )
    .format(
        date
    );

}


// ==========================================================
// INITIALS
// ==========================================================

function getInitials(
    firstName,
    lastName
) {

    return (
        `${firstName?.[0] || ""}${lastName?.[0] || ""}`
    )
    .toUpperCase();

}


// ==========================================================
// MONTH NAME
// ==========================================================

function getMonthName(
    month
) {

    const months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ];


    return (
        months[
            Number(month) - 1
        ]
        ||
        "Contribution"
    );

}


// ==========================================================
// ERROR DISPLAY
// ==========================================================

function showError(
    message
) {

    errorBox.textContent =
        message;


    errorBox.classList.remove(
        "hidden"
    );


    errorBox.scrollIntoView(
        {
            behavior: "smooth",
            block: "center"
        }
    );

}


function hideError() {

    errorBox.textContent =
        "";


    errorBox.classList.add(
        "hidden"
    );

}


// ==========================================================
// SUCCESS DISPLAY
// ==========================================================

function showContributionSuccess(
    message
) {

    contributionSuccess.textContent =
        message;


    contributionSuccess.classList.remove(
        "hidden"
    );

}


function hideContributionSuccess() {

    contributionSuccess.textContent =
        "";


    contributionSuccess.classList.add(
        "hidden"
    );

}


// ==========================================================
// CONTRIBUTION LOADING STATE
// ==========================================================

function setContributionLoading(
    loading
) {

    addContributionButton.disabled =
        loading;


    cancelEditButton.disabled =
        loading;


    if (loading) {

        addContributionButton.textContent =
            currentEditingContributionId
            !== null
            ?
            "Saving Changes..."
            :
            "Saving Contribution...";

    }

    else {

        addContributionButton.textContent =
            currentEditingContributionId
            !== null
            ?
            "Save Changes"
            :
            "Add Contribution";

    }

}
// ==========================================================
// PROFILE EDITING
// ==========================================================

function startProfileEdit() {

    hideError();

    hideProfileSuccess();


    if (!currentMemberData) {

        showError(
            "Member profile information is unavailable."
        );

        return;

    }


    document.getElementById(
        "profile-first-name-input"
    ).value =
        currentMemberData.first_name;


    document.getElementById(
        "profile-last-name-input"
    ).value =
        currentMemberData.last_name;


    document.getElementById(
        "profile-dob-input"
    ).value =
        currentMemberData.date_of_birth;


    document.getElementById(
        "profile-sex-input"
    ).value =
        currentMemberData.sex;


    document.getElementById(
        "profile-contribution-months-input"
    ).value =
        document.getElementById(
            "metric-months"
        ).textContent
        .replaceAll(
            ",",
            ""
        );


    document.getElementById(
        "profile-salary-input"
    ).value =
        currentMemberData
        .best_three_year_average_annual_salary;


    profileDisplay.classList.add(
        "hidden"
    );


    profileForm.classList.remove(
        "hidden"
    );


    editProfileButton.classList.add(
        "hidden"
    );

}


// ==========================================================
// CANCEL PROFILE EDIT
// ==========================================================

function cancelProfileEdit() {

    profileForm.reset();


    profileForm.classList.add(
        "hidden"
    );


    profileDisplay.classList.remove(
        "hidden"
    );


    editProfileButton.classList.remove(
        "hidden"
    );


    hideProfileSuccess();

}


// ==========================================================
// SAVE PROFILE
// ==========================================================

async function saveProfile(
    event
) {

    event.preventDefault();


    hideError();

    hideProfileSuccess();


    if (!currentMemberId) {

        showError(
            "No authenticated member profile is available."
        );

        return;

    }


    const firstName =
        document.getElementById(
            "profile-first-name-input"
        ).value
        .trim();


    const lastName =
        document.getElementById(
            "profile-last-name-input"
        ).value
        .trim();


    const dateOfBirth =
        document.getElementById(
            "profile-dob-input"
        ).value;


    const sex =
        document.getElementById(
            "profile-sex-input"
        ).value;


    const contributionMonths =
        Number(
            document.getElementById(
                "profile-contribution-months-input"
            ).value
        );


    const salary =
        Number(
            document.getElementById(
                "profile-salary-input"
            ).value
        );


    if (
        !firstName
        ||
        !lastName
    ) {

        showError(
            "First name and last name are required."
        );

        return;

    }


    if (!dateOfBirth) {

        showError(
            "Date of birth is required."
        );

        return;

    }


    const selectedDate =
        new Date(
            `${dateOfBirth}T00:00:00`
        );


    if (
        selectedDate
        >
        new Date()
    ) {

        showError(
            "Date of birth cannot be in the future."
        );

        return;

    }


    if (
        sex !== "Male"
        &&
        sex !== "Female"
    ) {

        showError(
            "Please select a valid sex."
        );

        return;

    }


    if (
        !Number.isInteger(
            contributionMonths
        )
        ||
        contributionMonths < 0
    ) {

        showError(
            "Contribution months must be a whole number greater than or equal to zero."
        );

        return;

    }
    const maximumContributionMonths =
    getMaximumPlausibleContributionMonths(
        dateOfBirth
    );

if (
    contributionMonths
    >
    maximumContributionMonths
) {
    showError(
        "Contribution months are not plausible for your age."
    );

    return;
}


    if (
        !Number.isFinite(
            salary
        )
        ||
        salary < 0
    ) {

        showError(
            "Salary must be zero or greater."
        );

        return;

    }
    if (
    !hasAtMostTwoDecimalPlaces(
        salary
    )
) {
    showError(
        "Salary cannot have more than 2 decimal places."
    );

    return;
}


    setProfileLoading(
        true
    );


    try {

        const response =
            await authenticatedFetch(
                `${API_BASE_URL}/members/${currentMemberId}`,
                {

                    method: "PUT",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {

                                first_name:
                                    firstName,

                                last_name:
                                    lastName,

                                date_of_birth:
                                    dateOfBirth,

                                sex:
                                    sex,

                                contribution_months:
                                    contributionMonths,

                                best_three_year_average_annual_salary:
                                    salary

                            }
                        )

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    "Unable to update your profile."
                )
            );

        }


        profileForm.classList.add(
            "hidden"
        );


        profileDisplay.classList.remove(
            "hidden"
        );


        editProfileButton.classList.remove(
            "hidden"
        );


        await refreshCurrentDashboard();


        showProfileSuccess(
            "Profile updated successfully."
        );

    }

    catch (error) {

        showError(
            error.message
        );

    }

    finally {

        setProfileLoading(
            false
        );

    }

}


// ==========================================================
// PROFILE LOADING
// ==========================================================

function setProfileLoading(
    loading
) {

    saveProfileButton.disabled =
        loading;


    cancelProfileButton.disabled =
        loading;


    saveProfileButton.textContent =
        loading
        ?
        "Saving Profile..."
        :
        "Save Profile";

}


// ==========================================================
// PROFILE SUCCESS
// ==========================================================

function showProfileSuccess(
    message
) {

    profileSuccess.textContent =
        message;


    profileSuccess.classList.remove(
        "hidden"
    );

}


function hideProfileSuccess() {

    profileSuccess.textContent =
        "";


    profileSuccess.classList.add(
        "hidden"
    );

}

// ==========================================================
// START APPLICATION
// ==========================================================

initialiseDashboard();

function hasAtMostTwoDecimalPlaces(
    value
) {
    if (!Number.isFinite(value)) {
        return false;
    }

    const valueAsText =
        String(value);

    if (!valueAsText.includes(".")) {
        return true;
    }

    const decimalPart =
        valueAsText.split(".")[1];

    return decimalPart.length <= 2;
}
function calculateAge(
    dateOfBirth
) {
    const birthDate =
        new Date(
            `${dateOfBirth}T00:00:00`
        );

    const today =
        new Date();

    let age =
        today.getFullYear()
        -
        birthDate.getFullYear();

    const monthDifference =
        today.getMonth()
        -
        birthDate.getMonth();

    if (
        monthDifference < 0
        ||
        (
            monthDifference === 0
            &&
            today.getDate()
            <
            birthDate.getDate()
        )
    ) {
        age -= 1;
    }

    return age;
}

function isContributionPeriodPlausibleForDob(
    dateOfBirth,
    year,
    month
) {
    const birthDate =
        new Date(
            `${dateOfBirth}T00:00:00`
        );

    const earliestYear =
        birthDate.getFullYear() + 15;

    const earliestMonth =
        birthDate.getMonth() + 1;

    if (year < earliestYear) {
        return false;
    }

    if (
        year === earliestYear
        &&
        month < earliestMonth
    ) {
        return false;
    }

    return true;
}


function getMaximumPlausibleContributionMonths(
    dateOfBirth
) {
    const age =
        calculateAge(
            dateOfBirth
        );

    return Math.max(
        0,
        (age - 15 + 1) * 12
    );
}