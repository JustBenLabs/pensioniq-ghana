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
        await loadSavedRetirementPlan();
        await loadSavedRetirementGoal();


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


    displayRetirementReadiness(
        data.retirement_readiness
    );

    prepareRetirementScenario(
    data.member
);

prepareRetirementGoal(
    data.member
);


    displayContributionSummary(
        data.contribution_summary
    );


    displayContributionHealth(
        data.contribution_health
    );

}

// ==========================================================
// RETIREMENT READINESS
// ==========================================================


function displayRetirementReadiness(
    readiness
) {

    if (!readiness) {
        return;
    }


    // ------------------------------------------------------
    // DOM ELEMENTS
    // ------------------------------------------------------

    const scoreElement =
        document.getElementById(
            "readiness-score"
        );

    const ratingElement =
        document.getElementById(
            "readiness-rating"
        );

    const messageElement =
        document.getElementById(
            "readiness-score-message"
        );

    const progressBar =
        document.getElementById(
            "readiness-progress-bar"
        );


    const eligibilityScore =
        document.getElementById(
            "readiness-eligibility-score"
        );

    const pensionScore =
        document.getElementById(
            "readiness-pension-score"
        );

    const consistencyScore =
        document.getElementById(
            "readiness-consistency-score"
        );


    const minimumStatus =
        document.getElementById(
            "readiness-minimum-status"
        );

    const minimumDetail =
        document.getElementById(
            "readiness-minimum-detail"
        );


    const maximumStatus =
        document.getElementById(
            "readiness-maximum-status"
        );

    const maximumDetail =
        document.getElementById(
            "readiness-maximum-detail"
        );


    const continuityElement =
        document.getElementById(
            "readiness-continuity"
        );

    const continuityDetail =
        document.getElementById(
            "readiness-continuity-detail"
        );


    const dataQualityElement =
        document.getElementById(
            "readiness-data-quality"
        );

    const dataQualityDetail =
        document.getElementById(
            "readiness-data-quality-detail"
        );


    const recommendationList =
        document.getElementById(
            "readiness-recommendation-list"
        );

    const disclaimerElement =
        document.getElementById(
            "readiness-disclaimer"
        );


    // ------------------------------------------------------
    // BASIC VALUES
    // ------------------------------------------------------

    const score =
        readiness.score !== null
            ?
            Number(
                readiness.score
            )
            :
            null;


    scoreElement.textContent =
        score !== null
            ?
            score.toFixed(2)
            :
            "Incomplete";


    ratingElement.textContent =
        readiness.rating
        ||
        "Incomplete";


    // ------------------------------------------------------
    // STATUS BADGE
    // ------------------------------------------------------

    ratingElement.classList.remove(
        "status-success",
        "status-warning",
        "status-danger",
        "readiness-status-fair"
    );


    switch (
        readiness.rating
    ) {

        case "Strong":

        case "Good":

            ratingElement.classList.add(
                "status-success"
            );

            break;


        case "Fair":

            ratingElement.classList.add(
                "readiness-status-fair"
            );

            break;


        case "Building":

        case "Incomplete":

            ratingElement.classList.add(
                "status-warning"
            );

            break;


        case "Needs Attention":

            ratingElement.classList.add(
                "status-danger"
            );

            break;

    }


    // ------------------------------------------------------
    // MAIN MESSAGE
    // ------------------------------------------------------

    if (
        readiness.provisional
    ) {

        messageElement.textContent =
            (
                "Your readiness score is incomplete "
                +
                "because PensionIQ does not yet have "
                +
                "enough aligned contribution-history "
                +
                "data to assess consistency."
            );

    }

    else if (
        readiness.rating
        ===
        "Strong"
    ) {

        messageElement.textContent =
            (
                "Your recorded retirement position "
                +
                "is strong under the PensionIQ "
                +
                "readiness framework."
            );

    }

    else if (
        readiness.rating
        ===
        "Good"
    ) {

        messageElement.textContent =
            (
                "Your retirement position is progressing "
                +
                "well. Continue strengthening your "
                +
                "contribution record."
            );

    }

    else if (
        readiness.rating
        ===
        "Fair"
    ) {

        messageElement.textContent =
            (
                "You are making meaningful retirement "
                +
                "progress, with room to strengthen "
                +
                "your position."
            );

    }

    else if (
        readiness.rating
        ===
        "Building"
    ) {

        messageElement.textContent =
            (
                "Your retirement position is still "
                +
                "being built. Focus on contribution "
                +
                "progress and consistency."
            );

    }

    else {

        messageElement.textContent =
            (
                "Your retirement position currently "
                +
                "needs attention. Review the guidance "
                +
                "below for priority actions."
            );

    }


    // ------------------------------------------------------
    // SCORE PROGRESS BAR
    // ------------------------------------------------------

    const progressPercent =
        score === null
            ?
            0
            :
            Math.max(
                0,
                Math.min(
                    100,
                    score
                )
            );


    progressBar.style.width =
        `${progressPercent}%`;


    // ------------------------------------------------------
    // SCORE COMPONENTS
    // ------------------------------------------------------

    eligibilityScore.textContent =
        (
            readiness.components
            ?.eligibility
            ?.score
            ??
            "0.00"
        )
        +
        " / 40";


    pensionScore.textContent =
        (
            readiness.components
            ?.pension_right
            ?.score
            ??
            "0.00"
        )
        +
        " / 35";


    const consistencyValue =
        readiness.components
        ?.contribution_consistency
        ?.score;


    consistencyScore.textContent =
        consistencyValue !== null
        &&
        consistencyValue !== undefined
            ?
            `${consistencyValue} / 25`
            :
            "Not assessed";


    // ------------------------------------------------------
    // MINIMUM THRESHOLD
    // ------------------------------------------------------

    if (
        readiness.months_to_minimum
        ===
        0
    ) {

        minimumStatus.textContent =
            "Reached";

        minimumDetail.textContent =
            (
                "The minimum 180-month contribution "
                +
                "threshold has been reached."
            );

    }

    else {

        minimumStatus.textContent =
            (
                `${readiness.months_to_minimum} `
                +
                "months remaining"
            );

        minimumDetail.textContent =
            (
                "Additional qualifying contributions "
                +
                "are needed to reach the 180-month "
                +
                "minimum threshold."
            );

    }


    // ------------------------------------------------------
    // MAXIMUM PENSION-RIGHT LEVEL
    // ------------------------------------------------------

    if (
        readiness.months_to_maximum
        ===
        0
    ) {

        maximumStatus.textContent =
            "Reached";

        maximumDetail.textContent =
            (
                "The 420-month maximum pension-right "
                +
                "level has been reached."
            );

    }

    else {

        maximumStatus.textContent =
            (
                `${readiness.months_to_maximum} `
                +
                "months remaining"
            );

        maximumDetail.textContent =
            (
                "Qualifying contributions can continue "
                +
                "increasing pension-right progress "
                +
                "until this level is reached."
            );

    }


    // ------------------------------------------------------
    // CONTINUITY
    // ------------------------------------------------------

    const dataQuality =
        readiness.data_quality
        ||
        {};


    const continuityPercent =
        dataQuality
        .continuity_ratio_percent;


    continuityElement.textContent =
        continuityPercent !== null
        &&
        continuityPercent !== undefined
            ?
            `${continuityPercent}%`
            :
            "Not available";


    if (
        dataQuality
        .continuity_used_in_score
    ) {

        continuityDetail.textContent =
            (
                "This continuity result is included "
                +
                "in your readiness score."
            );

    }

    else {

        continuityDetail.textContent =
            (
                "This value is not currently being "
                +
                "used in your readiness score."
            );

    }


    // ------------------------------------------------------
    // DATA QUALITY
    // ------------------------------------------------------

    const alignmentStatus =
        dataQuality
        .record_alignment_status;


    if (
        alignmentStatus
        ===
        "ALIGNED"
    ) {

        dataQualityElement.textContent =
            "Aligned";

        dataQualityDetail.textContent =
            (
                "Your detailed contribution records "
                +
                "align with your stored contribution "
                +
                "month total."
            );

    }

    else if (
        alignmentStatus
        ===
        "NO_DETAILED_HISTORY"
    ) {

        dataQualityElement.textContent =
            "More data needed";

        dataQualityDetail.textContent =
            (
                "Add your detailed monthly contribution "
                +
                "history to complete the consistency "
                +
                "assessment."
            );

    }

    else {

        dataQualityElement.textContent =
            "Review needed";

        dataQualityDetail.textContent =
            (
                "Your detailed records and stored "
                +
                "contribution-month total do not "
                +
                "currently align."
            );

    }


    // ------------------------------------------------------
    // PERSONALIZED RECOMMENDATIONS
    // ------------------------------------------------------

    recommendationList.replaceChildren();


    const recommendations =
        Array.isArray(
            readiness.recommendations
        )
            ?
            readiness.recommendations
            :
            [];


    recommendations.forEach(
        (
            recommendation
        ) => {

            const item =
                document.createElement(
                    "li"
                );


            const marker =
                document.createElement(
                    "span"
                );

            marker.className =
                "readiness-recommendation-marker";

            marker.textContent =
                "✓";


            const text =
                document.createElement(
                    "p"
                );

            text.textContent =
                recommendation;


            item.append(
                marker,
                text
            );


            recommendationList.append(
                item
            );

        }
    );


    if (
        recommendations.length
        ===
        0
    ) {

        const item =
            document.createElement(
                "li"
            );


        const text =
            document.createElement(
                "p"
            );

        text.textContent =
            (
                "No additional retirement guidance "
                +
                "is available at this time."
            );


        item.append(
            text
        );


        recommendationList.append(
            item
        );

    }


    // ------------------------------------------------------
    // DISCLAIMER
    // ------------------------------------------------------

    disclaimerElement.textContent =
        readiness.disclaimer
        ||
        (
            "This is a PensionIQ retirement-planning "
            +
            "indicator and is not an official SSNIT "
            +
            "benefit determination."
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


    container.replaceChildren();


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


    body.replaceChildren();


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


        const periodCell =
            document.createElement(
                "td"
            );

        periodCell.textContent =
            `${check.month_name} ${check.year}`;


        const earningsCell =
            document.createElement(
                "td"
            );

        earningsCell.textContent =
            formatCurrency(
                check.insurable_earnings
            );


        const recordedCell =
            document.createElement(
                "td"
            );

        recordedCell.textContent =
            (
                check.recorded_first_tier
                !== null
            )
                ?
                formatCurrency(
                    check.recorded_first_tier
                )
                :
                "\u2014";


        const expectedCell =
            document.createElement(
                "td"
            );

        expectedCell.textContent =
            (
                check.expected_first_tier
                !== null
            )
                ?
                formatCurrency(
                    check.expected_first_tier
                )
                :
                "\u2014";


        const differenceCell =
            document.createElement(
                "td"
            );

        differenceCell.textContent =
            (
                check.difference
                !== null
            )
                ?
                formatCurrency(
                    check.difference
                )
                :
                "\u2014";


        const statusCell =
            document.createElement(
                "td"
            );


        const statusBadge =
            document.createElement(
                "span"
            );


        let statusClassName =
            "check-status";


        if (
            check.status ===
            "MATCHED"
        ) {

            statusClassName +=
                " check-matched";

        }
        else if (
            check.status ===
            "AMOUNT_MISMATCH"
        ) {

            statusClassName +=
                " check-danger";

        }
        else {

            statusClassName +=
                " check-warning";

        }


        statusBadge.className =
            statusClassName;


        statusBadge.textContent =
            formatStatus(
                check.status
            );


        statusCell.appendChild(
            statusBadge
        );


        row.append(
            periodCell,
            earningsCell,
            recordedCell,
            expectedCell,
            differenceCell,
            statusCell
        );


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


    body.replaceChildren();


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


            const periodCell =
    document.createElement(
        "td"
    );

periodCell.textContent =
    `${getMonthName(record.month)} ${record.year}`;


const earningsCell =
    document.createElement(
        "td"
    );

earningsCell.textContent =
    formatCurrency(
        record.insurable_earnings
    );


const contributionCell =
    document.createElement(
        "td"
    );

contributionCell.textContent =
    (
        record
        .recorded_first_tier_contribution
        !== null
    )
        ?
        formatCurrency(
            record
            .recorded_first_tier_contribution
        )
        :
        "\u2014";


const actionsCell =
    document.createElement(
        "td"
    );


const actions =
    document.createElement(
        "div"
    );

actions.className =
    "table-actions";


const editButton =
    document.createElement(
        "button"
    );

editButton.type =
    "button";

editButton.className =
    "action-button edit-button";

editButton.dataset.action =
    "edit";

editButton.dataset.id =
    String(record.id);

editButton.textContent =
    "Edit";


const deleteButton =
    document.createElement(
        "button"
    );

deleteButton.type =
    "button";

deleteButton.className =
    "action-button delete-button";

deleteButton.dataset.action =
    "delete";

deleteButton.dataset.id =
    String(record.id);

deleteButton.textContent =
    "Delete";


actions.append(
    editButton,
    deleteButton
);


actionsCell.appendChild(
    actions
);


row.append(
    periodCell,
    earningsCell,
    contributionCell,
    actionsCell
);


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

// ==========================================================
// WHAT-IF RETIREMENT PLANNER
// ==========================================================


function prepareRetirementScenario(
    member
) {

    if (!member) {
        return;
    }


    const monthsElement =
        document.getElementById(
            "scenario-current-months"
        );


    const salaryElement =
        document.getElementById(
            "scenario-current-salary"
        );


    const salaryInput =
        document.getElementById(
            "scenario-projected-salary"
        );


    if (monthsElement) {

        monthsElement.textContent =
            Number(
                member.contribution_months
                ||
                0
            )
            .toLocaleString();

    }


    if (salaryElement) {

        salaryElement.textContent =
            formatScenarioCurrency(
                member
                .best_three_year_average_annual_salary
            );

    }


    if (
        salaryInput
        &&
        document.activeElement
        !==
        salaryInput
    ) {

        salaryInput.value =
            Number(
                member
                .best_three_year_average_annual_salary
                ||
                0
            )
            .toFixed(
                2
            );

    }

}

// ==========================================================
// SAVED SCENARIO STATE
// ==========================================================


let lastSuccessfulScenarioAssumptions = null;

let currentSavedRetirementPlan = null;


function setScenarioSavePlanStatus(
    message,
    type = "success"
) {

    const status =
        document.getElementById(
            "scenario-save-plan-status"
        );


    if (!status) {
        return;
    }


    status.textContent =
        message;


    status.classList.remove(
        "hidden",
        "success",
        "error"
    );


    status.classList.add(
        type
    );

}


function hideScenarioSavePlanStatus() {

    const status =
        document.getElementById(
            "scenario-save-plan-status"
        );


    if (!status) {
        return;
    }


    status.textContent = "";

    status.classList.add(
        "hidden"
    );

}

// ==========================================================
// LOAD SAVED RETIREMENT PLAN
// ==========================================================


async function loadSavedRetirementPlan() {

    if (!currentMemberId) {
        return;
    }


    const saveButton =
        document.getElementById(
            "scenario-save-plan-button"
        );


    const deleteButton =
        document.getElementById(
            "scenario-delete-plan-button"
        );


    try {

        const response =
            await authenticatedFetch(

                (
                    `${API_BASE_URL}/members/`
                    +
                    `${currentMemberId}/`
                    +
                    "retirement-plan"
                )

            );


        if (response.status === 404) {

            currentSavedRetirementPlan =
                null;


            if (deleteButton) {

                deleteButton.classList.add(
                    "hidden"
                );

            }


            return;

        }


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    "Unable to load your saved retirement plan."
                )
            );

        }


        currentSavedRetirementPlan =
            data;


        if (deleteButton) {

    deleteButton.classList.toggle(

        "hidden",

        !(
            data.scenario
            &&
            data.scenario.saved
        )

    );

}


        // --------------------------------------------------
        // No What-If scenario is saved.
        // The row may contain only a Goal Planner plan.
        // --------------------------------------------------

        if (
            !data.scenario
            ||
            !data.scenario.saved
        ) {

            return;

        }


        // --------------------------------------------------
        // Restore saved assumptions into form
        // --------------------------------------------------

        const monthsInput =
            document.getElementById(
                "scenario-additional-months"
            );


        const salaryInput =
            document.getElementById(
                "scenario-projected-salary"
            );


        const ageInput =
            document.getElementById(
                "scenario-retirement-age"
            );


        if (monthsInput) {

            monthsInput.value =
                data.scenario
                .additional_contribution_months;

        }


        if (salaryInput) {

            salaryInput.value =
                data.scenario
                .projected_annual_salary;

        }


        if (ageInput) {

            ageInput.value =
                data.scenario
                .retirement_age;

        }


        // --------------------------------------------------
        // Saved assumptions are still valid.
        // GET already freshly recalculated them.
        // --------------------------------------------------

        if (
            data.scenario.calculation_status
            ===
            "CALCULATED"
            &&
            data.scenario.result
        ) {

            lastSuccessfulScenarioAssumptions = {

                additional_contribution_months:
                    data.scenario
                    .additional_contribution_months,

                projected_annual_salary:
                    data.scenario
                    .projected_annual_salary,

                retirement_age:
                    data.scenario
                    .retirement_age

            };


            displayRetirementScenario({

    ...data.scenario.result,

    assumptions: {

        additional_contribution_months:
            data.scenario
            .additional_contribution_months,

        projected_annual_salary:
            data.scenario
            .projected_annual_salary,

        retirement_age:
            data.scenario
            .retirement_age

    },

    data_quality:
        data.data_quality
        ||
        {}

});

            if (saveButton) {

                saveButton.disabled =
                    false;

                saveButton.textContent =
                    "Update Saved Plan";

            }


            setScenarioSavePlanStatus(
                "Saved retirement plan loaded and recalculated."
            );


            return;

        }


        // --------------------------------------------------
        // Saved assumptions exist but are no longer valid.
        // Preserve them so the member can review/delete them,
        // but require the scenario to be rerun before updating.
        // --------------------------------------------------

        lastSuccessfulScenarioAssumptions =
            null;


        if (saveButton) {

            saveButton.disabled =
                true;

            saveButton.textContent =
                "Update Saved Plan";

        }


        setScenarioSavePlanStatus(

            (
                data.scenario
                .calculation_error
                ||
                "Your saved scenario needs to be recalculated."
            ),

            "error"

        );

    }

    catch (error) {

        setScenarioSavePlanStatus(
            error.message,
            "error"
        );

    }

}


// ==========================================================
// RUN SCENARIO
// ==========================================================


async function runRetirementScenario(
    event
) {

    event.preventDefault();


    hideScenarioError();


    if (!currentMemberId) {

        showScenarioError(
            "No authenticated member profile is available."
        );

        return;

    }


    const monthsInput =
        document.getElementById(
            "scenario-additional-months"
        );


    const salaryInput =
        document.getElementById(
            "scenario-projected-salary"
        );


    const ageInput =
        document.getElementById(
            "scenario-retirement-age"
        );


    const additionalMonths =
        Number(
            monthsInput.value
        );


    const projectedSalary =
        Number(
            salaryInput.value
        );


    const retirementAge =
        Number(
            ageInput.value
        );


    // ------------------------------------------------------
    // FRONTEND VALIDATION
    // ------------------------------------------------------


    if (
        !Number.isInteger(
            additionalMonths
        )
        ||
        additionalMonths < 0
    ) {

        showScenarioError(
            "Additional contribution months must be a whole number of zero or greater."
        );

        return;

    }


    if (
        !Number.isFinite(
            projectedSalary
        )
        ||
        projectedSalary < 0
    ) {

        showScenarioError(
            "Projected annual salary must be zero or greater."
        );

        return;

    }


    if (
        !Number.isInteger(
            retirementAge
        )
        ||
        retirementAge < 55
        ||
        retirementAge > 60
    ) {

        showScenarioError(
            "Retirement age must be between 55 and 60."
        );

        return;

    }


    setScenarioLoading(
        true
    );


    try {

        const response =
            await authenticatedFetch(

                (
                    `${API_BASE_URL}/members/`
                    +
                    `${currentMemberId}/`
                    +
                    "retirement-scenario"
                ),

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

                                additional_contribution_months:
                                    additionalMonths,

                                projected_annual_salary:
                                    projectedSalary
                                        .toFixed(
                                            2
                                        ),

                                retirement_age:
                                    retirementAge

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
                    "Unable to calculate the retirement scenario."
                )

            );

        }


        displayRetirementScenario(
            data
        );


        lastSuccessfulScenarioAssumptions = {

            additional_contribution_months:
                additionalMonths,

            projected_annual_salary:
                projectedSalary.toFixed(
                    2
                ),

            retirement_age:
                retirementAge

        };


        const savePlanButton =
            document.getElementById(
                "scenario-save-plan-button"
            );


        if (savePlanButton) {

            savePlanButton.disabled =
                false;

        }


        setScenarioSavePlanStatus(
            "Scenario ready to save."
        );

    }
    catch (error) {

        showScenarioError(
            error.message
        );

    }
    finally {

        setScenarioLoading(
            false
        );

    }

}

// ==========================================================
// SAVE WHAT-IF SCENARIO
// ==========================================================


async function saveRetirementScenarioPlan() {

    hideScenarioSavePlanStatus();


    if (!currentMemberId) {

        setScenarioSavePlanStatus(
            "No authenticated member profile is available.",
            "error"
        );

        return;

    }


    if (!lastSuccessfulScenarioAssumptions) {

        setScenarioSavePlanStatus(
            "Run a valid What-If scenario before saving.",
            "error"
        );

        return;

    }


    const saveButton =
        document.getElementById(
            "scenario-save-plan-button"
        );


    if (saveButton) {

        saveButton.disabled =
            true;

        saveButton.textContent =
            "Saving...";

    }


    try {

        const planUrl =
            (
                `${API_BASE_URL}/members/`
                +
                `${currentMemberId}/`
                +
                "retirement-plan"
            );


        // --------------------------------------------------
        // Check whether a plan already exists.
        //
        // This also lets us preserve a Goal Planner plan
        // if one is already stored in the same database row.
        // --------------------------------------------------

        const existingResponse =
            await authenticatedFetch(
                planUrl
            );


        let existingPlan = null;


        if (
            existingResponse.status
            ===
            200
        ) {

            existingPlan =
                await existingResponse.json();

        }

        else if (
            existingResponse.status
            !==
            404
        ) {

            const errorData =
                await existingResponse.json();


            throw new Error(
                getApiErrorMessage(
                    errorData,
                    "Unable to check the saved retirement plan."
                )
            );

        }


        // --------------------------------------------------
        // Scenario assumptions
        // --------------------------------------------------

        const payload = {

            scenario_additional_contribution_months:
                lastSuccessfulScenarioAssumptions
                .additional_contribution_months,

            scenario_projected_annual_salary:
                lastSuccessfulScenarioAssumptions
                .projected_annual_salary,

            scenario_retirement_age:
                lastSuccessfulScenarioAssumptions
                .retirement_age

        };


        // --------------------------------------------------
        // Preserve an existing saved Goal Planner analysis.
        //
        // PUT is a full replacement in our backend, so we
        // must not accidentally erase the goal assumptions.
        // --------------------------------------------------

        if (
            existingPlan
            &&
            existingPlan.goal
            &&
            existingPlan.goal.saved
        ) {

            payload.goal_target_monthly_pension =
                existingPlan
                .goal
                .target_monthly_pension;


            payload.goal_projected_annual_salary =
                existingPlan
                .goal
                .projected_annual_salary;


            payload.goal_retirement_age =
                existingPlan
                .goal
                .retirement_age;

        }


        const method =
            existingPlan
            ?
            "PUT"
            :
            "POST";


        const saveResponse =
            await authenticatedFetch(

                planUrl,

                {

                    method:
                        method,

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            payload
                        )

                }

            );


        const savedPlan =
            await saveResponse.json();


        if (!saveResponse.ok) {

            throw new Error(
                getApiErrorMessage(
                    savedPlan,
                    "Unable to save the retirement plan."
                )
            );

        }


        setScenarioSavePlanStatus(
            existingPlan
            ?
            "Saved retirement plan updated successfully."
            :
            "Retirement plan saved successfully."
        );
        currentSavedRetirementPlan =
    savedPlan;


const deleteButton =
    document.getElementById(
        "scenario-delete-plan-button"
    );


if (deleteButton) {

    deleteButton.classList.remove(
        "hidden"
    );

}


        if (saveButton) {

            saveButton.textContent =
                "Update Saved Plan";

        }

    }

    catch (error) {

        setScenarioSavePlanStatus(
            error.message,
            "error"
        );


        if (saveButton) {

            saveButton.textContent =
                "Save Plan";

        }

    }

    finally {

        if (saveButton) {

            saveButton.disabled =
                false;

        }

    }

}


// ==========================================================
// DELETE SAVED WHAT-IF SCENARIO
// ==========================================================


async function deleteSavedRetirementPlan() {

    hideScenarioSavePlanStatus();


    if (!currentMemberId) {

        setScenarioSavePlanStatus(
            "No authenticated member profile is available.",
            "error"
        );

        return;

    }


    const plan =
        currentSavedRetirementPlan;


    if (
        !plan
        ||
        !plan.scenario
        ||
        !plan.scenario.saved
    ) {

        setScenarioSavePlanStatus(
            "There is no saved What-If scenario to delete.",
            "error"
        );

        return;

    }


    const hasSavedGoal =
        Boolean(
            plan.goal
            &&
            plan.goal.saved
        );


    const confirmationMessage =
        hasSavedGoal
        ?
        (
            "Delete your saved What-If scenario? "
            +
            "Your saved retirement Goal will be kept."
        )
        :
        "Delete your saved What-If scenario?";


    if (
        !window.confirm(
            confirmationMessage
        )
    ) {

        return;

    }


    const deleteButton =
        document.getElementById(
            "scenario-delete-plan-button"
        );


    const saveButton =
        document.getElementById(
            "scenario-save-plan-button"
        );


    if (deleteButton) {

        deleteButton.disabled =
            true;

        deleteButton.textContent =
            "Deleting...";

    }


    try {

        const planUrl =
            (
                `${API_BASE_URL}/members/`
                +
                `${currentMemberId}/`
                +
                "retirement-plan"
            );


        let response;


        // --------------------------------------------------
        // Goal also exists.
        //
        // PUT is a full replacement, so preserve the Goal
        // while omitting the What-If scenario.
        // --------------------------------------------------


        if (hasSavedGoal) {

            const payload = {

                goal_target_monthly_pension:
                    plan.goal
                    .target_monthly_pension,

                goal_projected_annual_salary:
                    plan.goal
                    .projected_annual_salary,

                goal_retirement_age:
                    plan.goal
                    .retirement_age

            };


            response =
                await authenticatedFetch(

                    planUrl,

                    {

                        method:
                            "PUT",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                payload
                            )

                    }

                );

        }

        // --------------------------------------------------
        // Scenario is the only saved planner.
        // Remove the database row completely.
        // --------------------------------------------------

        else {

            response =
                await authenticatedFetch(

                    planUrl,

                    {
                        method:
                            "DELETE"
                    }

                );

        }


        let data =
            null;


        try {

            data =
                await response.json();

        }

        catch {

            data =
                null;

        }


        if (!response.ok) {

            throw new Error(

                getApiErrorMessage(

                    data,

                    "Unable to delete the saved What-If scenario."

                )

            );

        }


        // --------------------------------------------------
        // Update browser state
        // --------------------------------------------------


        currentSavedRetirementPlan =
            hasSavedGoal
            ?
            data
            :
            null;


        lastSuccessfulScenarioAssumptions =
            null;


        const results =
            document.getElementById(
                "scenario-results"
            );


        if (results) {

            results.classList.add(
                "hidden"
            );

        }


        if (deleteButton) {

            deleteButton.classList.add(
                "hidden"
            );

        }


        if (saveButton) {

            saveButton.disabled =
                true;

            saveButton.textContent =
                "Save Plan";

        }


        setScenarioSavePlanStatus(

            hasSavedGoal
            ?
            (
                "Saved What-If scenario deleted. "
                +
                "Your retirement Goal was kept."
            )
            :
            "Saved What-If scenario deleted."

        );

    }

    catch (error) {

        setScenarioSavePlanStatus(
            error.message,
            "error"
        );

    }

    finally {

        if (deleteButton) {

            deleteButton.disabled =
                false;

            deleteButton.textContent =
                "Delete Saved What-If";

        }

    }

}

// ==========================================================
// DISPLAY SCENARIO
// ==========================================================


function displayRetirementScenario(
    data
) {

    if (
        !data
        ||
        !data.baseline
        ||
        !data.scenario
    ) {

        showScenarioError(
            "The retirement scenario response is incomplete."
        );

        return;

    }


    const baseline =
        data.baseline;


    const scenario =
        data.scenario;


    const impact =
        data.impact
        ||
        {};


    const dataQuality =
        data.data_quality
        ||
        {};


    // ------------------------------------------------------
    // DATE
    // ------------------------------------------------------


    setScenarioText(
        "scenario-retirement-date",
        formatScenarioDate(
            scenario.retirement_date
        )
    );


    // ------------------------------------------------------
    // BASELINE
    // ------------------------------------------------------


    setScenarioText(
        "scenario-baseline-months",
        formatScenarioMonths(
            baseline.contribution_months
        )
    );


    setScenarioText(
        "scenario-baseline-right",
        formatScenarioPensionRight(
            baseline.pension_right_percent
        )
    );


    setScenarioText(
        "scenario-baseline-factor",
        formatScenarioFactor(
            baseline.retirement_age_factor
        )
    );


    setScenarioText(
        "scenario-baseline-pension",
        formatScenarioPension(
            baseline.monthly_pension
        )
    );


    setScenarioText(
        "scenario-baseline-readiness",
        formatScenarioReadiness(
            baseline.readiness_score,
            baseline.readiness_rating
        )
    );


    // ------------------------------------------------------
    // SCENARIO
    // ------------------------------------------------------


    setScenarioText(
        "scenario-projected-months",
        formatScenarioMonths(
            scenario.contribution_months
        )
    );


    setScenarioText(
        "scenario-projected-right",
        formatScenarioPensionRight(
            scenario.pension_right_percent
        )
    );


    setScenarioText(
        "scenario-projected-factor",
        formatScenarioFactor(
            scenario.retirement_age_factor
        )
    );


    setScenarioText(
        "scenario-projected-pension",
        formatScenarioPension(
            scenario.monthly_pension
        )
    );


    setScenarioText(
        "scenario-projected-readiness",
        formatScenarioReadiness(
            scenario.readiness_score,
            scenario.readiness_rating
        )
    );


    // ------------------------------------------------------
    // IMPACT
    // ------------------------------------------------------


    setScenarioText(
        "scenario-impact-months",
        (
            "+"
            +
            Number(
                data
                .assumptions
                .additional_contribution_months
                ||
                0
            )
            .toLocaleString()
            +
            " months"
        )
    );


    setScenarioText(
        "scenario-impact-right",
        formatScenarioPointChange(
            impact
            .pension_right_change_percentage_points
        )
    );


    setScenarioText(
        "scenario-impact-pension",
        formatScenarioCurrencyChange(
            impact.monthly_pension_change
        )
    );


    setScenarioText(
        "scenario-impact-pension-percent",
        formatScenarioPercentChange(
            impact
            .monthly_pension_change_percent
        )
    );


    setScenarioText(
        "scenario-impact-readiness",
        formatScenarioReadinessChange(
            impact
            .readiness_score_change
        )
    );


    setScenarioText(
        "scenario-impact-eligibility",
        (
            impact
            .became_monthly_pension_eligible
            ?
            "Reached monthly-pension threshold"
            :
            "No new eligibility transition"
        )
    );


    // ------------------------------------------------------
    // DATA QUALITY
    // ------------------------------------------------------


    displayScenarioDataQuality(
        dataQuality
    );


    // ------------------------------------------------------
    // DISCLAIMER
    // ------------------------------------------------------


    setScenarioText(
        "scenario-disclaimer",
        (
            data.disclaimer
            ||
            "This is a PensionIQ planning simulation and not an official SSNIT determination."
        )
    );


    // ------------------------------------------------------
    // SHOW RESULTS
    // ------------------------------------------------------


    const results =
        document.getElementById(
            "scenario-results"
        );


    if (results) {

        results.classList.remove(
            "hidden"
        );


        results.scrollIntoView(
            {
                behavior:
                    "smooth",

                block:
                    "nearest"
            }
        );

    }

}


// ==========================================================
// DATA QUALITY MESSAGE
// ==========================================================


function displayScenarioDataQuality(
    dataQuality
) {

    let message;


    if (
        dataQuality
        .continuity_used_in_scenario
        ===
        true
    ) {

        message =
            (
                "Your detailed contribution history aligns "
                +
                "with your stored contribution-month total. "
                +
                "The assessed contribution continuity was "
                +
                "therefore included in the readiness comparison."
            );

    }

    else if (
        dataQuality
        .record_alignment_status
        ===
        "NO_DETAILED_HISTORY"
    ) {

        message =
            (
                "No detailed contribution history is currently "
                +
                "available. Contribution consistency was not "
                +
                "used, so the readiness score in this scenario "
                +
                "remains incomplete."
            );

    }

    else if (
        dataQuality
        .record_alignment_status
        ===
        "TOTAL_AND_HISTORY_DIFFER"
    ) {

        message =
            (
                "Your stored contribution-month total does not "
                +
                "match the detailed contribution records currently "
                +
                "available. Contribution consistency was therefore "
                +
                "excluded to avoid overstating retirement readiness."
            );

    }

    else {

        message =
            (
                "Contribution consistency could not be reliably "
                +
                "assessed for this scenario."
            );

    }


    setScenarioText(
        "scenario-data-quality-message",
        message
    );

}


// ==========================================================
// SCENARIO FORM ERROR
// ==========================================================


function showScenarioError(
    message
) {

    const errorElement =
        document.getElementById(
            "scenario-form-error"
        );


    if (!errorElement) {
        return;
    }


    errorElement.textContent =
        message;


    errorElement.classList.remove(
        "hidden"
    );

}


function hideScenarioError() {

    const errorElement =
        document.getElementById(
            "scenario-form-error"
        );


    if (!errorElement) {
        return;
    }


    errorElement.textContent =
        "";


    errorElement.classList.add(
        "hidden"
    );

}


// ==========================================================
// LOADING STATE
// ==========================================================


function setScenarioLoading(
    isLoading
) {

    const button =
        document.getElementById(
            "scenario-submit-button"
        );


    if (!button) {
        return;
    }


    button.disabled =
        isLoading;


    button.textContent =
        (
            isLoading
            ?
            "Running Scenario..."
            :
            "Run What-If Scenario"
        );

}


// ==========================================================
// SAFE TEXT OUTPUT
// ==========================================================


function setScenarioText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    element.textContent =
        value;

}


// ==========================================================
// FORMATTERS
// ==========================================================


function formatScenarioCurrency(
    value
) {

    if (
        value === null
        ||
        value === undefined
        ||
        value === ""
    ) {

        return "Unavailable";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Unavailable";

    }


    return (
        "GH¢"
        +
        number.toLocaleString(
            "en-GH",
            {
                minimumFractionDigits:
                    2,

                maximumFractionDigits:
                    2
            }
        )
    );

}


function formatScenarioPension(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not yet eligible";

    }


    return (
        formatScenarioCurrency(
            value
        )
        +
        " / month"
    );

}


function formatScenarioPensionRight(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not yet eligible";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Unavailable";

    }


    return (
        number.toFixed(
            2
        )
        +
        "%"
    );

}


function formatScenarioFactor(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not applicable";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Unavailable";

    }


    return (
        (
            number
            *
            100
        )
        .toFixed(
            1
        )
        +
        "%"
    );

}


function formatScenarioReadiness(
    score,
    rating
) {

    if (
        score === null
        ||
        score === undefined
    ) {

        return (
            rating
            ||
            "Incomplete"
        );

    }


    const number =
        Number(
            score
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return (
            rating
            ||
            "Unavailable"
        );

    }


    return (
        number.toFixed(
            2
        )
        +
        " / 100 — "
        +
        (
            rating
            ||
            "Unrated"
        )
    );

}


function formatScenarioMonths(
    value
) {

    const number =
        Number(
            value
            ||
            0
        );


    return (
        number.toLocaleString()
        +
        " months"
    );

}


function formatScenarioPointChange(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not comparable";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Not comparable";

    }


    return (
        formatScenarioSignedNumber(
            number
        )
        +
        " percentage points"
    );

}


function formatScenarioCurrencyChange(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not comparable";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Not comparable";

    }


    const absoluteValue =
        Math.abs(
            number
        );


    if (number > 0) {

        return (
            "Increase of "
            +
            formatScenarioCurrency(
                absoluteValue
            )
        );

    }


    if (number < 0) {

        return (
            "Decrease of "
            +
            formatScenarioCurrency(
                absoluteValue
            )
        );

    }


    return "No change";

}

function formatScenarioPercentChange(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not comparable";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Not comparable";

    }


    const absoluteValue =
        Math.abs(
            number
        );


    if (number > 0) {

        return (
            "Increase of "
            +
            absoluteValue.toFixed(
                2
            )
            +
            "%"
        );

    }


    if (number < 0) {

        return (
            "Decrease of "
            +
            absoluteValue.toFixed(
                2
            )
            +
            "%"
        );

    }


    return "No change";

}


function formatScenarioReadinessChange(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Incomplete";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Incomplete";

    }


    return (
        formatScenarioSignedNumber(
            number
        )
        +
        " points"
    );

}


function formatScenarioSignedNumber(
    value
) {

    const prefix =
        (
            value > 0
            ?
            "+"
            :
            ""
        );


    return (
        prefix
        +
        value.toFixed(
            2
        )
    );

}


function formatScenarioDate(
    value
) {

    if (!value) {

        return "Retirement date unavailable";

    }


    const dateValue =
        new Date(
            `${value}T00:00:00`
        );


    if (
        Number.isNaN(
            dateValue.getTime()
        )
    ) {

        return value;

    }


    return (
        "Retirement: "
        +
        dateValue.toLocaleDateString(
            "en-GH",
            {
                year:
                    "numeric",

                month:
                    "short",

                day:
                    "numeric"
            }
        )
    );

}


// ==========================================================
// FORM EVENT
// ==========================================================


const retirementScenarioForm =
    document.getElementById(
        "retirement-scenario-form"
    );


if (retirementScenarioForm) {

    retirementScenarioForm.addEventListener(
        "submit",
        runRetirementScenario
    );

}

const scenarioSavePlanButton =
    document.getElementById(
        "scenario-save-plan-button"
    );


if (scenarioSavePlanButton) {

    scenarioSavePlanButton.addEventListener(
        "click",
        saveRetirementScenarioPlan
    );

}


const scenarioDeletePlanButton =
    document.getElementById(
        "scenario-delete-plan-button"
    );


if (scenarioDeletePlanButton) {

    scenarioDeletePlanButton.addEventListener(
        "click",
        deleteSavedRetirementPlan
    );

}

function invalidateScenarioSaveState() {

    if (!lastSuccessfulScenarioAssumptions) {
        return;
    }


    lastSuccessfulScenarioAssumptions =
        null;


    if (scenarioSavePlanButton) {

        scenarioSavePlanButton.disabled =
            true;

        scenarioSavePlanButton.textContent =
            "Save Plan";

    }


    hideScenarioSavePlanStatus();

}


if (retirementScenarioForm) {

    retirementScenarioForm.addEventListener(
        "input",
        invalidateScenarioSaveState
    );


    retirementScenarioForm.addEventListener(
        "change",
        invalidateScenarioSaveState
    );

}

// ==========================================================
// RETIREMENT GOAL PLANNER
// ==========================================================

let lastSuccessfulGoalAssumptions = null;

// ==========================================================
// SAVED GOAL RESULT ADAPTER
// ==========================================================


function savedGoalRatioToPercent(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return null;

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return null;

    }


    return (
        number
        *
        100
    )
    .toFixed(
        2
    );

}


function buildSavedGoalDisplayData(
    result
) {

    return {

        goal: {

            target_monthly_pension:
                result
                .target_monthly_pension,

            projected_annual_salary:
                result
                .projected_annual_salary,

            retirement_age:
                result
                .retirement_age,

            retirement_date:
                result
                .retirement_date,

            retirement_age_factor_percent:
                savedGoalRatioToPercent(
                    result
                    .retirement_age_factor
                )

        },


        current_position: {

            contribution_months:
                result
                .current_contribution_months,

            projected_monthly_pension:
                result
                .current_projected_monthly_pension,

            estimated_monthly_pension:
                result
                .current_projected_monthly_pension

        },


        contribution_capacity: {

            months_available_before_retirement:
                result
                .available_contribution_months,

            maximum_attainable_contribution_months:
                result
                .maximum_attainable_contribution_months

        },


        requirement: {

            required_contribution_months:
                result
                .required_contribution_months,

            additional_contribution_months_required:
                result
                .additional_contribution_months_required,

            estimated_monthly_pension:
                result
                .estimated_monthly_pension_at_required_months,

            pension_right_percent:
                savedGoalRatioToPercent(
                    result
                    .pension_right_at_required_months
                )

        },


        maximum_position: {

            contribution_months:
                result
                .maximum_attainable_contribution_months,

            estimated_monthly_pension:
                result
                .maximum_attainable_monthly_pension,

            pension_right_percent:
                savedGoalRatioToPercent(
                    result
                    .maximum_attainable_pension_right
                )

        },


        gap_analysis: {

            pension_gap_at_maximum:
                result
                .pension_gap_at_maximum,

            approximate_annual_salary_required:
                result
                .approximate_annual_salary_required_at_maximum_months

        },


        goal_result: {

            achievable:
                result
                .goal_achievable,

            status:
                result
                .goal_status

        }

    };

}

// ==========================================================
// LOAD SAVED RETIREMENT GOAL
// ==========================================================


async function loadSavedRetirementGoal() {

    const plan =
        currentSavedRetirementPlan;


    const deleteButton =
        document.getElementById(
            "goal-delete-plan-button"
        );


    if (deleteButton) {

        deleteButton.classList.add(
            "hidden"
        );

    }


    if (
        !plan
        ||
        !plan.goal
        ||
        !plan.goal.saved
    ) {

        return;

    }


    if (deleteButton) {

        deleteButton.classList.remove(
            "hidden"
        );

    }


    const savedGoal =
        plan.goal;


    const targetInput =
        document.getElementById(
            "goal-monthly-pension"
        );


    const salaryInput =
        document.getElementById(
            "goal-projected-salary"
        );


    const ageInput =
        document.getElementById(
            "goal-retirement-age"
        );


    const saveButton =
        document.getElementById(
            "goal-save-plan-button"
        );


    // ------------------------------------------------------
    // Restore saved assumptions
    // ------------------------------------------------------


    if (targetInput) {

        targetInput.value =
            savedGoal
            .target_monthly_pension;

    }


    if (salaryInput) {

        salaryInput.value =
            savedGoal
            .projected_annual_salary;

    }


    if (ageInput) {

        ageInput.value =
            savedGoal
            .retirement_age;

    }


    if (saveButton) {

        saveButton.textContent =
            "Update Saved Goal";

    }

    // ------------------------------------------------------
    // Saved goal was successfully recalculated by GET
    // ------------------------------------------------------


    if (
        savedGoal.calculation_status
        ===
        "CALCULATED"
        &&
        savedGoal.result
    ) {

        lastSuccessfulGoalAssumptions = {

            target_monthly_pension:
                savedGoal
                .target_monthly_pension,

            projected_annual_salary:
                savedGoal
                .projected_annual_salary,

            retirement_age:
                savedGoal
                .retirement_age

        };


        const displayData =
            buildSavedGoalDisplayData(
                savedGoal.result
            );


        displayRetirementGoal(
            displayData
        );


        if (saveButton) {

            saveButton.disabled =
                false;

        }


        setGoalSavePlanStatus(
            "Saved retirement goal loaded and recalculated."
        );


        return;

    }


    // ------------------------------------------------------
    // Saved assumptions still exist, but current engines
    // can no longer calculate them.
    // ------------------------------------------------------


    lastSuccessfulGoalAssumptions =
        null;


    if (saveButton) {

        saveButton.disabled =
            true;

    }


    setGoalSavePlanStatus(

        (
            savedGoal.error
            ||
            savedGoal.calculation_error
            ||
            "Your saved retirement goal needs to be recalculated."
        ),

        "error"

    );

}

function setGoalSavePlanStatus(
    message,
    type = "success"
) {

    const status =
        document.getElementById(
            "goal-save-plan-status"
        );


    if (!status) {
        return;
    }


    status.textContent =
        message;


    status.classList.remove(
        "hidden",
        "success",
        "error"
    );


    status.classList.add(
        type
    );

}


function hideGoalSavePlanStatus() {

    const status =
        document.getElementById(
            "goal-save-plan-status"
        );


    if (!status) {
        return;
    }


    status.textContent = "";

    status.classList.add(
        "hidden"
    );

}

function prepareRetirementGoal(
    member
) {

    if (!member) {
        return;
    }


    const salaryInput =
        document.getElementById(
            "goal-projected-salary"
        );


    if (
        salaryInput
        &&
        document.activeElement
        !==
        salaryInput
    ) {

        salaryInput.value =
            Number(
                member
                .best_three_year_average_annual_salary
                ||
                0
            )
            .toFixed(
                2
            );

    }

}


// ==========================================================
// RUN GOAL ANALYSIS
// ==========================================================


async function runRetirementGoal(
    event
) {

    event.preventDefault();


    hideGoalError();


    if (!currentMemberId) {

        showGoalError(
            "No authenticated member profile is available."
        );

        return;

    }


    const targetInput =
        document.getElementById(
            "goal-monthly-pension"
        );


    const salaryInput =
        document.getElementById(
            "goal-projected-salary"
        );


    const ageInput =
        document.getElementById(
            "goal-retirement-age"
        );


    const target =
        Number(
            targetInput.value
        );


    const salary =
        Number(
            salaryInput.value
        );


    const retirementAge =
        Number(
            ageInput.value
        );


    if (
        !Number.isFinite(
            target
        )
        ||
        target <= 0
    ) {

        showGoalError(
            "Target monthly pension must be greater than zero."
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

        showGoalError(
            "Projected annual salary must be zero or greater."
        );

        return;

    }


    if (
        !Number.isInteger(
            retirementAge
        )
        ||
        retirementAge < 55
        ||
        retirementAge > 60
    ) {

        showGoalError(
            "Retirement age must be between 55 and 60."
        );

        return;

    }


    setGoalLoading(
        true
    );


    try {

        const response =
            await authenticatedFetch(

                (
                    `${API_BASE_URL}/members/`
                    +
                    `${currentMemberId}/`
                    +
                    "retirement-goal"
                ),

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

                                target_monthly_pension:
                                    target.toFixed(
                                        2
                                    ),

                                projected_annual_salary:
                                    salary.toFixed(
                                        2
                                    ),

                                retirement_age:
                                    retirementAge

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
                    "Unable to analyse your retirement goal."
                )

            );

        }


        displayRetirementGoal(
            data
        );

        lastSuccessfulGoalAssumptions = {

    target_monthly_pension:
        target.toFixed(
            2
        ),

    projected_annual_salary:
        salary.toFixed(
            2
        ),

    retirement_age:
        retirementAge

};


const goalSaveButton =
    document.getElementById(
        "goal-save-plan-button"
    );


if (goalSaveButton) {

    goalSaveButton.disabled =
        false;


    goalSaveButton.textContent =
        (
            currentSavedRetirementPlan
            &&
            currentSavedRetirementPlan.goal
            &&
            currentSavedRetirementPlan.goal.saved
        )
        ?
        "Update Saved Goal"
        :
        "Save Goal";

}


setGoalSavePlanStatus(
    "Goal analysis ready to save."
);
       }

    catch (error) {

        showGoalError(
            error.message
        );

    }

    finally {

        setGoalLoading(
            false
        );

    }

}

// ==========================================================
// SAVE RETIREMENT GOAL
// ==========================================================


async function saveRetirementGoalPlan() {

    hideGoalSavePlanStatus();


    if (!currentMemberId) {

        setGoalSavePlanStatus(
            "No authenticated member profile is available.",
            "error"
        );

        return;

    }


    if (!lastSuccessfulGoalAssumptions) {

        setGoalSavePlanStatus(
            "Analyse a valid retirement goal before saving.",
            "error"
        );

        return;

    }


    const saveButton =
        document.getElementById(
            "goal-save-plan-button"
        );


    if (saveButton) {

        saveButton.disabled =
            true;

        saveButton.textContent =
            "Saving...";

    }


    try {

        const planUrl =
            (
                `${API_BASE_URL}/members/`
                +
                `${currentMemberId}/`
                +
                "retirement-plan"
            );


        // --------------------------------------------------
        // Load existing saved plan first.
        // --------------------------------------------------

        const existingResponse =
            await authenticatedFetch(
                planUrl
            );


        let existingPlan =
            null;


        if (
            existingResponse.status
            ===
            200
        ) {

            existingPlan =
                await existingResponse.json();

        }

        else if (
            existingResponse.status
            !==
            404
        ) {

            const errorData =
                await existingResponse.json();


            throw new Error(
                getApiErrorMessage(
                    errorData,
                    "Unable to check the saved retirement plan."
                )
            );

        }


        // --------------------------------------------------
        // Goal assumptions
        // --------------------------------------------------

        const payload = {

            goal_target_monthly_pension:
                lastSuccessfulGoalAssumptions
                .target_monthly_pension,

            goal_projected_annual_salary:
                lastSuccessfulGoalAssumptions
                .projected_annual_salary,

            goal_retirement_age:
                lastSuccessfulGoalAssumptions
                .retirement_age

        };


        // --------------------------------------------------
        // Preserve an existing What-If scenario.
        //
        // PUT replaces the complete saved-plan assumptions,
        // therefore the scenario must be included again.
        // --------------------------------------------------

        if (
            existingPlan
            &&
            existingPlan.scenario
            &&
            existingPlan.scenario.saved
        ) {

            payload
                .scenario_additional_contribution_months =
                    existingPlan
                    .scenario
                    .additional_contribution_months;


            payload
                .scenario_projected_annual_salary =
                    existingPlan
                    .scenario
                    .projected_annual_salary;


            payload
                .scenario_retirement_age =
                    existingPlan
                    .scenario
                    .retirement_age;

        }


        const method =
            existingPlan
            ?
            "PUT"
            :
            "POST";


        const response =
            await authenticatedFetch(

                planUrl,

                {

                    method:
                        method,

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            payload
                        )

                }

            );


        const savedPlan =
            await response.json();


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    savedPlan,
                    "Unable to save the retirement goal."
                )
            );

        }


        currentSavedRetirementPlan =
            savedPlan;


        setGoalSavePlanStatus(
            existingPlan
            ?
            "Saved retirement goal updated successfully."
            :
            "Retirement goal saved successfully."
        );


        if (saveButton) {

            saveButton.textContent =
                "Update Saved Goal";

        }

    }

    catch (error) {

        setGoalSavePlanStatus(
            error.message,
            "error"
        );


        if (saveButton) {

            saveButton.textContent =
                (
                    currentSavedRetirementPlan
                    &&
                    currentSavedRetirementPlan.goal
                    &&
                    currentSavedRetirementPlan.goal.saved
                )
                ?
                "Update Saved Goal"
                :
                "Save Goal";

        }

    }

    finally {

        if (saveButton) {

            saveButton.disabled =
                false;

        }

    }

}

// ==========================================================
// DELETE SAVED RETIREMENT GOAL
// ==========================================================


async function deleteSavedRetirementGoalPlan() {

    hideGoalSavePlanStatus();


    if (!currentMemberId) {

        setGoalSavePlanStatus(
            "No authenticated member profile is available.",
            "error"
        );

        return;

    }


    const plan =
        currentSavedRetirementPlan;


    if (
        !plan
        ||
        !plan.goal
        ||
        !plan.goal.saved
    ) {

        setGoalSavePlanStatus(
            "There is no saved retirement Goal to delete.",
            "error"
        );

        return;

    }


    const hasSavedScenario =
        Boolean(
            plan.scenario
            &&
            plan.scenario.saved
        );


    const confirmationMessage =
        hasSavedScenario
        ?
        (
            "Delete your saved retirement Goal? "
            +
            "Your saved What-If scenario will be kept."
        )
        :
        "Delete your saved retirement Goal?";


    if (
        !window.confirm(
            confirmationMessage
        )
    ) {

        return;

    }


    const deleteButton =
        document.getElementById(
            "goal-delete-plan-button"
        );


    const saveButton =
        document.getElementById(
            "goal-save-plan-button"
        );


    if (deleteButton) {

        deleteButton.disabled =
            true;

        deleteButton.textContent =
            "Deleting...";

    }


    try {

        const planUrl =
            (
                `${API_BASE_URL}/members/`
                +
                `${currentMemberId}/`
                +
                "retirement-plan"
            );


        let response;


        // --------------------------------------------------
        // What-If also exists.
        //
        // Preserve it and remove only the Goal.
        // --------------------------------------------------


        if (hasSavedScenario) {

            const payload = {

                scenario_additional_contribution_months:
                    plan.scenario
                    .additional_contribution_months,

                scenario_projected_annual_salary:
                    plan.scenario
                    .projected_annual_salary,

                scenario_retirement_age:
                    plan.scenario
                    .retirement_age

            };


            response =
                await authenticatedFetch(

                    planUrl,

                    {

                        method:
                            "PUT",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                payload
                            )

                    }

                );

        }

        // --------------------------------------------------
        // Goal is the only saved planner.
        // --------------------------------------------------

        else {

            response =
                await authenticatedFetch(

                    planUrl,

                    {
                        method:
                            "DELETE"
                    }

                );

        }


        let data =
            null;


        try {

            data =
                await response.json();

        }

        catch {

            data =
                null;

        }


        if (!response.ok) {

            throw new Error(

                getApiErrorMessage(

                    data,

                    "Unable to delete the saved retirement Goal."

                )

            );

        }


        // --------------------------------------------------
        // Update browser state
        // --------------------------------------------------


        currentSavedRetirementPlan =
            hasSavedScenario
            ?
            data
            :
            null;


        lastSuccessfulGoalAssumptions =
            null;


        const results =
            document.getElementById(
                "goal-results"
            );


        if (results) {

            results.classList.add(
                "hidden"
            );

        }


        if (deleteButton) {

            deleteButton.classList.add(
                "hidden"
            );

        }


        if (saveButton) {

            saveButton.disabled =
                true;

            saveButton.textContent =
                "Save Goal";

        }


        setGoalSavePlanStatus(

            hasSavedScenario
            ?
            (
                "Saved retirement Goal deleted. "
                +
                "Your What-If scenario was kept."
            )
            :
            "Saved retirement Goal deleted."

        );

    }

    catch (error) {

        setGoalSavePlanStatus(
            error.message,
            "error"
        );

    }

    finally {

        if (deleteButton) {

            deleteButton.disabled =
                false;

            deleteButton.textContent =
                "Delete Saved Goal";

        }

    }

}

// ==========================================================
// DISPLAY GOAL RESULT
// ==========================================================


function displayRetirementGoal(
    data
) {

    const goal =
        data.goal
        ||
        {};


    const current =
        data.current_position
        ||
        {};


    const capacity =
        data.contribution_capacity
        ||
        {};


    const requirement =
        data.requirement
        ||
        {};


    const maximum =
        data.maximum_position
        ||
        {};


    const gap =
        data.gap_analysis
        ||
        {};


    const result =
        data.goal_result
        ||
        {};


    // ------------------------------------------------------
    // SUMMARY
    // ------------------------------------------------------


    setGoalText(
        "goal-result-target",
        (
            formatGoalCurrency(
                goal.target_monthly_pension
            )
            +
            " / month"
        )
    );


    setGoalText(
        "goal-result-age",
        (
            goal.retirement_age
            +
            " years"
        )
    );


    setGoalText(
        "goal-result-date",
        formatGoalDate(
            goal.retirement_date
        )
    );


    setGoalText(
        "goal-result-salary",
        formatGoalCurrency(
            goal.projected_annual_salary
        )
    );


    // ------------------------------------------------------
    // STATUS
    // ------------------------------------------------------


    setGoalStatus(
        result.status,
        result.achievable
    );


    // ------------------------------------------------------
    // ACHIEVABLE PANEL
    // ------------------------------------------------------


    setGoalText(
        "goal-current-months",
        (
            Number(
                current.contribution_months
                ||
                0
            )
            .toLocaleString()
            +
            " months"
        )
    );


    setGoalText(
        "goal-required-months",
        formatGoalMonths(
            requirement
            .required_contribution_months
        )
    );


    setGoalText(
        "goal-additional-months",
        formatGoalAdditionalMonths(
            requirement
            .additional_contribution_months_required
        )
    );


    setGoalText(
        "goal-required-right",
        formatGoalPercentage(
            requirement
            .pension_right_percent
        )
    );


    setGoalText(
        "goal-required-pension",
        formatGoalPension(
            requirement
            .estimated_monthly_pension
        )
    );


    setGoalText(
        "goal-months-available",
        (
            Number(
                capacity
                .months_available_before_retirement
                ||
                0
            )
            .toLocaleString()
            +
            " months"
        )
    );


    // ------------------------------------------------------
    // MAXIMUM / GAP PANEL
    // ------------------------------------------------------


    setGoalText(
        "goal-maximum-months",
        formatGoalMonths(
            maximum
            .contribution_months
        )
    );


    setGoalText(
        "goal-maximum-right",
        formatGoalPercentage(
            maximum
            .pension_right_percent
        )
    );


    setGoalText(
        "goal-maximum-pension",
        formatGoalPension(
            maximum
            .estimated_monthly_pension
        )
    );


    setGoalText(
        "goal-pension-gap",
        formatGoalPension(
            gap
            .pension_gap_at_maximum
        )
    );


    setGoalText(
        "goal-required-salary",
        (
            gap
            .approximate_annual_salary_required
            ===
            null
            ?
            "Not applicable"
            :
            formatGoalCurrency(
                gap
                .approximate_annual_salary_required
            )
        )
    );


    setGoalText(
        "goal-disclaimer-text",
        (
            data.disclaimer
            ||
            "This is a PensionIQ retirement-planning simulation."
        )
    );


    const results =
        document.getElementById(
            "goal-results"
        );


    if (results) {

        results.classList.remove(
            "hidden"
        );

    }

}


// ==========================================================
// GOAL STATUS
// ==========================================================


function setGoalStatus(
    status,
    achievable
) {

    const heading =
        document.getElementById(
            "goal-result-heading"
        );


    const message =
        document.getElementById(
            "goal-result-message"
        );


    const badge =
        document.getElementById(
            "goal-status-badge"
        );


    const achievablePanel =
        document.getElementById(
            "goal-achievable-panel"
        );


    const adjustmentPanel =
        document.getElementById(
            "goal-adjustment-panel"
        );


    if (
        achievablePanel
        &&
        adjustmentPanel
    ) {

        achievablePanel.classList.add(
            "hidden"
        );

        adjustmentPanel.classList.add(
            "hidden"
        );

    }


    let headingText;
    let messageText;
    let badgeText;


    switch (status) {

        case "ALREADY_ACHIEVABLE":

            headingText =
                "Your goal is already achievable";

            messageText =
                (
                    "At the salary and retirement age you selected, "
                    +
                    "your current contribution-month total already "
                    +
                    "supports the pension target in this simulation."
                );

            badgeText =
                "Already Achievable";

            if (achievablePanel) {

                achievablePanel.classList.remove(
                    "hidden"
                );

            }

            break;


        case "ACHIEVABLE":

            headingText =
                "Your goal is achievable";

            messageText =
                (
                    "PensionIQ found an estimated contribution-month "
                    +
                    "total that reaches your target before the "
                    +
                    "selected retirement age."
                );

            badgeText =
                "Achievable";

            if (achievablePanel) {

                achievablePanel.classList.remove(
                    "hidden"
                );

            }

            break;


        case "NOT_ACHIEVABLE_WITH_PROJECTED_SALARY":

            headingText =
                "Your goal needs adjustment";

            messageText =
                (
                    "The target cannot be reached with the selected "
                    +
                    "salary assumption by contribution months alone. "
                    +
                    "PensionIQ has shown the remaining gap and an "
                    +
                    "approximate salary basis that may be required."
                );

            badgeText =
                "Needs Adjustment";

            if (adjustmentPanel) {

                adjustmentPanel.classList.remove(
                    "hidden"
                );

            }

            break;


        case "MONTHLY_PENSION_THRESHOLD_UNREACHABLE":

            headingText =
                "Monthly pension threshold not reachable";

            messageText =
                (
                    "There is not enough modeled time before the "
                    +
                    "selected retirement age to reach the minimum "
                    +
                    "contribution-month threshold for a monthly "
                    +
                    "old-age pension."
                );

            badgeText =
                "Threshold Unreachable";

            if (adjustmentPanel) {

                adjustmentPanel.classList.remove(
                    "hidden"
                );

            }

            break;


        default:

            headingText =
                "Goal analysis completed";

            messageText =
                "Review the estimated retirement goal results below.";

            badgeText =
                achievable
                ?
                "Achievable"
                :
                "Review Required";

    }


    if (heading) {

        heading.textContent =
            headingText;

    }


    if (message) {

        message.textContent =
            messageText;

    }


    if (badge) {

        badge.textContent =
            badgeText;

    }

}


// ==========================================================
// GOAL FORMATTERS
// ==========================================================


function formatGoalCurrency(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Unavailable";

    }


    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "Unavailable";

    }


    return (
        "GH¢"
        +
        number.toLocaleString(
            "en-GH",
            {
                minimumFractionDigits:
                    2,

                maximumFractionDigits:
                    2
            }
        )
    );

}


function formatGoalPension(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not available";

    }


    return (
        formatGoalCurrency(
            value
        )
        +
        " / month"
    );

}


function formatGoalPercentage(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not available";

    }


    const number =
        Number(
            value
        );


    if (!Number.isFinite(number)) {

        return "Not available";

    }


    return (
        number.toFixed(
            2
        )
        +
        "%"
    );

}


function formatGoalMonths(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not available";

    }


    return (
        Number(
            value
        )
        .toLocaleString()
        +
        " months"
    );

}


function formatGoalAdditionalMonths(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "Not available";

    }


    const months =
        Number(
            value
        );


    if (months === 0) {

        return "No additional months required";

    }


    return (
        "+"
        +
        months.toLocaleString()
        +
        " months"
    );

}


function formatGoalDate(
    value
) {

    if (!value) {

        return "Unavailable";

    }


    const dateValue =
        new Date(
            `${value}T00:00:00`
        );


    if (
        Number.isNaN(
            dateValue.getTime()
        )
    ) {

        return value;

    }


    return dateValue.toLocaleDateString(
        "en-GH",
        {
            day:
                "numeric",

            month:
                "short",

            year:
                "numeric"
        }
    );

}


// ==========================================================
// SAFE TEXT OUTPUT
// ==========================================================


function setGoalText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (element) {

        element.textContent =
            value;

    }

}


// ==========================================================
// ERROR
// ==========================================================


function showGoalError(
    message
) {

    const element =
        document.getElementById(
            "goal-form-error"
        );


    if (!element) {
        return;
    }


    element.textContent =
        message;


    element.classList.remove(
        "hidden"
    );

}


function hideGoalError() {

    const element =
        document.getElementById(
            "goal-form-error"
        );


    if (!element) {
        return;
    }


    element.textContent =
        "";


    element.classList.add(
        "hidden"
    );

}


// ==========================================================
// LOADING
// ==========================================================


function setGoalLoading(
    isLoading
) {

    const button =
        document.getElementById(
            "goal-submit-button"
        );


    if (!button) {
        return;
    }


    button.disabled =
        isLoading;


    button.textContent =
        (
            isLoading
            ?
            "Analysing Goal..."
            :
            "Analyse My Goal"
        );

}


// ==========================================================
// FORM EVENT
// ==========================================================


const retirementGoalForm =
    document.getElementById(
        "retirement-goal-form"
    );


if (retirementGoalForm) {

    retirementGoalForm.addEventListener(
        "submit",
        runRetirementGoal
    );

}

const goalSavePlanButton =
    document.getElementById(
        "goal-save-plan-button"
    );


if (goalSavePlanButton) {

    goalSavePlanButton.addEventListener(
        "click",
        saveRetirementGoalPlan
    );

}
const goalDeletePlanButton =
    document.getElementById(
        "goal-delete-plan-button"
    );


if (goalDeletePlanButton) {

    goalDeletePlanButton.addEventListener(
        "click",
        deleteSavedRetirementGoalPlan
    );

}


function invalidateGoalSaveState() {

    if (!lastSuccessfulGoalAssumptions) {
        return;
    }


    lastSuccessfulGoalAssumptions =
        null;


    if (goalSavePlanButton) {

        goalSavePlanButton.disabled =
            true;


        goalSavePlanButton.textContent =
            (
                currentSavedRetirementPlan
                &&
                currentSavedRetirementPlan.goal
                &&
                currentSavedRetirementPlan.goal.saved
            )
            ?
            "Update Saved Goal"
            :
            "Save Goal";

    }


    hideGoalSavePlanStatus();

}


if (retirementGoalForm) {

    retirementGoalForm.addEventListener(
        "input",
        invalidateGoalSaveState
    );


    retirementGoalForm.addEventListener(
        "change",
        invalidateGoalSaveState
    );

}
// ==========================================================
// PERSONAL RETIREMENT REPORT
// ==========================================================


async function downloadRetirementReport() {

    hideRetirementReportError();


    if (!currentMemberId) {

        showRetirementReportError(
            "No authenticated member profile is available."
        );

        return;

    }


    setRetirementReportLoading(
        true
    );


    try {

        const response =
            await authenticatedFetch(

                (
                    `${API_BASE_URL}/members/`
                    +
                    `${currentMemberId}/`
                    +
                    "retirement-report.pdf"
                ),

                {
                    method:
                        "GET"
                }

            );


        // --------------------------------------------------
        // HANDLE API ERROR
        // --------------------------------------------------

        if (!response.ok) {

            let errorMessage =
                (
                    "Unable to generate your "
                    +
                    "retirement report."
                );


            try {

                const errorData =
                    await response.json();


                if (
                    errorData
                    &&
                    errorData.detail
                ) {

                    errorMessage =
                        errorData.detail;

                }

            }

            catch (error) {

                // Keep the fallback message when
                // the response is not JSON.

            }


            throw new Error(
                errorMessage
            );

        }


        // --------------------------------------------------
        // PDF
        // --------------------------------------------------

        const pdfBlob =
            await response.blob();


        if (
            !pdfBlob
            ||
            pdfBlob.size === 0
        ) {

            throw new Error(
                "The generated retirement report was empty."
            );

        }


        // --------------------------------------------------
        // TEMPORARY DOWNLOAD URL
        // --------------------------------------------------

        const downloadUrl =
            URL.createObjectURL(
                pdfBlob
            );


        const downloadLink =
            document.createElement(
                "a"
            );


        downloadLink.href =
            downloadUrl;


        downloadLink.download =
            "PensionIQ-Retirement-Report.pdf";


        downloadLink.style.display =
            "none";


        document.body.appendChild(
            downloadLink
        );


        downloadLink.click();


        downloadLink.remove();


        // Give the browser a short moment to
        // start the download before releasing
        // the object URL.

        window.setTimeout(
            () => {

                URL.revokeObjectURL(
                    downloadUrl
                );

            },
            1000
        );

    }

    catch (error) {

        console.error(
            "Retirement report download failed:",
            error
        );


        showRetirementReportError(

            error.message
            ||
            (
                "Unable to download your "
                +
                "retirement report."
            )

        );

    }

    finally {

        setRetirementReportLoading(
            false
        );

    }

}


// ==========================================================
// REPORT ERROR
// ==========================================================


function showRetirementReportError(
    message
) {

    const element =
        document.getElementById(
            "retirement-report-error"
        );


    if (!element) {
        return;
    }


    element.textContent =
        message;


    element.classList.remove(
        "hidden"
    );

}


function hideRetirementReportError() {

    const element =
        document.getElementById(
            "retirement-report-error"
        );


    if (!element) {
        return;
    }


    element.textContent =
        "";


    element.classList.add(
        "hidden"
    );

}


// ==========================================================
// REPORT LOADING STATE
// ==========================================================


function setRetirementReportLoading(
    isLoading
) {

    const button =
        document.getElementById(
            "download-retirement-report-button"
        );


    if (!button) {
        return;
    }


    button.disabled =
        isLoading;


    button.textContent =
        (
            isLoading
            ?
            "Generating Report..."
            :
            "Download Retirement Report"
        );

}


// ==========================================================
// REPORT BUTTON
// ==========================================================


const retirementReportButton =
    document.getElementById(
        "download-retirement-report-button"
    );


if (retirementReportButton) {

    retirementReportButton.addEventListener(

        "click",

        downloadRetirementReport

    );

}