const API_BASE_URL =
    "http://127.0.0.1:8000";


const registerForm =
    document.getElementById(
        "register-form"
    );


const registerButton =
    document.getElementById(
        "register-button"
    );


const errorBox =
    document.getElementById(
        "register-error"
    );


const successBox =
    document.getElementById(
        "register-success"
    );


// ==========================================================
// REGISTER
// ==========================================================

registerForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        hideMessages();


        const firstName =
            document.getElementById(
                "first-name"
            ).value
            .trim();


        const lastName =
            document.getElementById(
                "last-name"
            ).value
            .trim();


        const email =
            document.getElementById(
                "email"
            ).value
            .trim();


        const dateOfBirth =
            document.getElementById(
                "date-of-birth"
            ).value;


        const sex =
            document.getElementById(
                "sex"
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


        const password =
            document.getElementById(
                "password"
            ).value;


        const confirmPassword =
            document.getElementById(
                "confirm-password"
            ).value;


        // --------------------------------------------------
        // Validation
        // --------------------------------------------------

        if (
            !firstName
            ||
            !lastName
            ||
            !email
            ||
            !dateOfBirth
            ||
            !sex
        ) {

            showError(
                "Please complete all required fields."
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
                "Contribution months must be zero or greater."
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
                "Salary cannot be negative."
            );

            return;

        }


        if (
            password.length < 8
        ) {

            showError(
                "Password must contain at least 8 characters."
            );

            return;

        }


        if (
            password !==
            confirmPassword
        ) {

            showError(
                "The passwords do not match."
            );

            return;

        }


        setLoading(true);


        try {

            const response =
                await fetch(
                    `${API_BASE_URL}/auth/register`,
                    {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                {

                                    email:
                                        email,

                                    password:
                                        password,

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
                        "Unable to create account."
                    )
                );

            }


            showSuccess(
                "Account created successfully. Redirecting to sign in..."
            );


            registerForm.reset();


            // ----------------------------------------------
            // Move to login after a short delay
            // ----------------------------------------------

            setTimeout(
                () => {

                    window.location.href =
                        `login.html?email=${encodeURIComponent(email)}`;

                },
                1200
            );

        }

        catch (error) {

            showError(
                error.message
            );

        }

        finally {

            setLoading(false);

        }

    }
);


// ==========================================================
// HELPERS
// ==========================================================

function getApiErrorMessage(
    data,
    fallback
) {

    if (
        data
        &&
        typeof data.detail
        ===
        "string"
    ) {

        return data.detail;

    }


    if (
        data
        &&
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


    return fallback;

}


function showError(
    message
) {

    errorBox.textContent =
        message;


    errorBox.classList.remove(
        "hidden"
    );


    successBox.classList.add(
        "hidden"
    );

}


function showSuccess(
    message
) {

    successBox.textContent =
        message;


    successBox.classList.remove(
        "hidden"
    );


    errorBox.classList.add(
        "hidden"
    );

}


function hideMessages() {

    errorBox.classList.add(
        "hidden"
    );


    successBox.classList.add(
        "hidden"
    );

}


function setLoading(
    loading
) {

    registerButton.disabled =
        loading;


    registerButton.textContent =
        loading
        ?
        "Creating Account..."
        :
        "Create Account";

}