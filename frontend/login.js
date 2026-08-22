const API_BASE_URL =
    "http://127.0.0.1:8000";


const loginForm =
    document.getElementById(
        "login-form"
    );


const loginButton =
    document.getElementById(
        "login-button"
    );


const errorBox =
    document.getElementById(
        "login-error"
    );


// ==========================================================
// REDIRECT IF ALREADY AUTHENTICATED
// ==========================================================

if (
    sessionStorage.getItem(
        "pensioniq_access_token"
    )
) {

    window.location.href =
        "dashboard.html";

}
const queryParameters =
    new URLSearchParams(
        window.location.search
    );


const registeredEmail =
    queryParameters.get(
        "email"
    );


if (registeredEmail) {

    document.getElementById(
        "email"
    ).value =
        registeredEmail;

}


// ==========================================================
// LOGIN
// ==========================================================

loginForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        hideError();


        const email =
            document.getElementById(
                "email"
            ).value
            .trim();


        const password =
            document.getElementById(
                "password"
            ).value;


        if (
            !email
            ||
            !password
        ) {

            showError(
                "Please enter your email and password."
            );

            return;

        }


        setLoading(true);


        try {

            const response =
                await fetch(
                    `${API_BASE_URL}/auth/login`,
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
                                        password
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
                        "Unable to sign in."
                    )
                );

            }


            if (!data.access_token) {

                throw new Error(
                    "The server did not return an access token."
                );

            }


            // ----------------------------------------------
            // Store JWT for this browser session
            // ----------------------------------------------

            sessionStorage.setItem(
                "pensioniq_access_token",
                data.access_token
            );


            // ----------------------------------------------
            // Open dashboard
            // ----------------------------------------------

            window.location.href =
                "dashboard.html";

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

}


function hideError() {

    errorBox.textContent =
        "";


    errorBox.classList.add(
        "hidden"
    );

}


function setLoading(
    loading
) {

    loginButton.disabled =
        loading;


    loginButton.textContent =
        loading
        ?
        "Signing In..."
        :
        "Sign In";

}