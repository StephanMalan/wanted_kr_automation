import getpass

from wanted import Listing, UserInput, Config, Session, ProfileData, Terminal


if __name__ == "__main__":
    Terminal.log("Running https://www.wanted.co.kr automation script")
    cfg = Config.load_from_file()
    if not cfg:
        cfg = UserInput.prompt_user_for_config()
        cfg.save_to_file()

    if cfg.token and cfg.token_exp and cfg.check_token_validity():
        Terminal.log_task_success("Using cached token")
        session = Session.from_token(cfg.token, cfg.token_exp)
    else:
        password = getpass.getpass(prompt="  Enter your wanted.co.kr password: ")
        session = Session.from_credentials(cfg.email, password)
        cfg.cache_session(session)

    profile_data = ProfileData.get_session_data(session)

    listings = Listing.retrieve_listings(cfg, session)
    listings = Listing.filter_listings(listings, session)
    Listing.apply_to_listings(listings, session, profile_data)
