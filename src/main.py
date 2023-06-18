import getpass

from src import config, listing, logging, session, user_input

if __name__ == "__main__":
    print("Running https://www.wanted.co.kr automation script")
    cfg = config.Config.load_from_file()
    if not cfg:
        cfg = user_input.prompt_user_for_config()

    # Get session data
    if not cfg.check_token_validity():
        password = getpass.getpass(prompt="  Enter your wanted.co.kr password: ")
        token, expiry = session.login(cfg.email, password)
        cfg.cache_token_data(token, expiry)
        session_data = session.get_session_data(token)
    else:
        logging.log_task_success("Using cached token")
        assert cfg.token
        session_data = session.get_session_data(cfg.token)

    listings = listing.retrieve_listings(cfg, session_data)
    listings = listing.filter_listings(listings, cfg, session_data)
    listing.apply_to_listings(listings, session_data)
