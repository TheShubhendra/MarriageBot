import functools

import aiohttp_session
from aiohttp.web import HTTPFound, Request


def add_output_args():
    """This function is a wrapper around all routes. It takes the output and
    adds the user info and request to the returning dictionary
    It must be applied before the template decorator"""

    def inner_wrapper(func):
        """An inner wrapper so I can get args at the outer level"""

        @functools.wraps(func)
        async def wrapper(request: Request):
            """This is the wrapper that does all the heavy lifting"""

            # Run function
            data = await func(request)

            # See if we return anything other than data (like redirects)
            if isinstance(data, HTTPFound):
                if data.location == "/discord_oauth_login":
                    session = await aiohttp_session.get_session(request)
                    if "redirect_on_login" not in session:
                        session["redirect_on_login"] = str(request.url)
            if not isinstance(data, dict):
                return data

            # See if we need to get rid of them
            session = await aiohttp_session.get_session(request)
            login_redirect = session.pop("redirect_on_login", None)
            if login_redirect:
                return HTTPFound(location=login_redirect)

            # Update jinja params
            if data is None:
                data = dict()
            data.update({"session": session})
            if "user_info" not in data:
                try:
                    data.update({"user_info": session["user_info"]})
                except KeyError:
                    data.update({"user_info": None})
            if "request" not in data:
                data.update({"request": request})

            # # Check return relevant info
            # if redirect_if_logged_out and session.get('user_id') is None:
            #     return HTTPFound(location=redirect_if_logged_out)
            # elif redirect_if_logged_in and session.get('user_id') is not None:
            #     return HTTPFound(location=redirect_if_logged_in)

            # Update OpenGraph information
            if "opengraph" not in data:
                data.update({"opengraph": dict()})
            og_data = data["opengraph"].copy()
            og_data["og:title"] = og_data.get(
                "og:title", "MarriageBot - A marriage-based Discord bot"
            )
            og_data["og:description"] = og_data.get(
                "og:description",
                "MarriageBot is a Discord bot used for simulations of your family, be it that you want b1nzy as your mom, or Jake as your nephew, MarriageBot can handle it all.",
            )
            og_data["og:type"] = og_data.get("og:type", "website")
            og_data["og:image"] = og_data.get(
                "og:image",
                "https://marriagebot.xyz/static/images/MarriageBotCircle.150.png",
            )
            og_data["og:locale"] = og_data.get("og:locale", "en_GB")
            data["opengraph"] = og_data

            return data

        return wrapper

    return inner_wrapper
