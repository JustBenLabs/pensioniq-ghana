// ==========================================================
// PENSIONIQ GHANA
// FORGOT PASSWORD
// ==========================================================


const API_BASE_URL =
    window.PENSIONIQ_API_BASE_URL;


const forgotPasswordForm =
    document.getElementById(
        "forgot-password-form"
    );


const forgotPasswordButton =
    document.getElementById(
        "forgot-password-button"
    );


const forgotError =
    document.getElementById(
        "forgot-error"
    );


const forgotSuccess =
    document.getElementById(
        "forgot-success"
    );


// ==========================================================
// SUBMIT
// ==========================================================

forgotPasswordForm.addEventListener(
    "submit",
    requestPasswordReset
);


async function requestPasswordReset(
    event
) {

    event.preventDefault();

    hideMessages();


    const email =
        document.getElementById(
            "email"
        ).value
        .trim();


    if (!email) {

        showError(
            "Please enter your email address."
        );

        return;

    }


    setLoading(true);


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/auth/forgot-password`,
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
                                    email
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
                    "Unable to process your password-reset request."
                )
            );

        }


        showSuccess(
            data.message
            ||
            (
                "If an account exists for this email address, "
                +
                "password reset instructions have been generated."
            )
        );


        forgotPasswordForm.reset();

    }

    catch (error) {

        console.error(
            "Password reset request error:",
            error
        );


        showError(
            error.message
            ||
            "Unable to connect to PensionIQ."
        );

    }

    finally {

        setLoading(false);

    }

}


// ==========================================================
// HELPERS
// ==========================================================

function setLoading(
    loading
) {

    forgotPasswordButton.disabled =
        loading;


    forgotPasswordButton.textContent =
        loading
        ?
        "Processing..."
        :
        "Send Reset Instructions";

}


function showError(
    message
) {

    forgotError.textContent =
        message;


    forgotError.classList.remove(
        "hidden"
    );


    forgotSuccess.classList.add(
        "hidden"
    );

}


function showSuccess(
    message
) {

    forgotSuccess.textContent =
        message;


    forgotSuccess.classList.remove(
        "hidden"
    );


    forgotError.classList.add(
        "hidden"
    );

}


function hideMessages() {

    forgotError.textContent =
        "";


    forgotSuccess.textContent =
        "";


    forgotError.classList.add(
        "hidden"
    );


    forgotSuccess.classList.add(
        "hidden"
    );

}


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