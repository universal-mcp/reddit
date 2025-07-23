import httpx
from loguru import logger
from typing import Any

from universal_mcp.applications import APIApplication
from universal_mcp.exceptions import NotAuthorizedError
from universal_mcp.integrations import Integration


class RedditApp(APIApplication):
    def __init__(self, integration: Integration) -> None:
        super().__init__(name="reddit", integration=integration)
        self.base_api_url = "https://oauth.reddit.com"
        self.base_url = "https://oauth.reddit.com"

    def _post(self, url, data):
        try:
            headers = self._get_headers()
            response = httpx.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response
        except NotAuthorizedError as e:
            logger.warning(f"Authorization needed: {e.message}")
            raise e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return e.response.text or "Rate limit exceeded. Please try again later."
            else:
                raise e
        except Exception as e:
            logger.error(f"Error posting {url}: {e}")
            raise e

    def _get_headers(self):
        if not self.integration:
            raise ValueError("Integration not configured for RedditApp")
        credentials = self.integration.get_credentials()
        if "access_token" not in credentials:
            logger.error("Reddit credentials found but missing 'access_token'.")
            raise ValueError("Invalid Reddit credentials format.")

        return {
            "Authorization": f"Bearer {credentials['access_token']}",
            "User-Agent": "agentr-reddit-app/0.1 by AgentR",
        }

    def get_subreddit_posts(
        self, subreddit: str, limit: int = 5, timeframe: str = "day"
    ) -> str:
        """
        Retrieves and formats top posts from a specified subreddit within a given timeframe using the Reddit API

        Args:
            subreddit: The name of the subreddit (e.g., 'python', 'worldnews') without the 'r/' prefix
            limit: The maximum number of posts to return (default: 5, max: 100)
            timeframe: The time period for top posts. Valid options: 'hour', 'day', 'week', 'month', 'year', 'all' (default: 'day')

        Returns:
            A formatted string containing a numbered list of top posts, including titles, authors, scores, and URLs, or an error message if the request fails

        Raises:
            RequestException: When the HTTP request to the Reddit API fails
            JSONDecodeError: When the API response contains invalid JSON

        Tags:
            fetch, reddit, api, list, social-media, important, read-only
        """
        valid_timeframes = ["hour", "day", "week", "month", "year", "all"]
        if timeframe not in valid_timeframes:
            return f"Error: Invalid timeframe '{timeframe}'. Please use one of: {', '.join(valid_timeframes)}"
        if not 1 <= limit <= 100:
            return (
                f"Error: Invalid limit '{limit}'. Please use a value between 1 and 100."
            )
        url = f"{self.base_api_url}/r/{subreddit}/top"
        params = {"limit": limit, "t": timeframe}
        logger.info(
            f"Requesting top {limit} posts from r/{subreddit} for timeframe '{timeframe}'"
        )
        response = self._get(url, params=params)
        data = response.json()
        if "error" in data:
            logger.error(
                f"Reddit API error: {data['error']} - {data.get('message', '')}"
            )
            return f"Error from Reddit API: {data['error']} - {data.get('message', '')}"
        posts = data.get("data", {}).get("children", [])
        if not posts:
            return (
                f"No top posts found in r/{subreddit} for the timeframe '{timeframe}'."
            )
        result_lines = [
            f"Top {len(posts)} posts from r/{subreddit} (timeframe: {timeframe}):\n"
        ]
        for i, post_container in enumerate(posts):
            post = post_container.get("data", {})
            title = post.get("title", "No Title")
            score = post.get("score", 0)
            author = post.get("author", "Unknown Author")
            permalink = post.get("permalink", "")
            full_url = f"https://www.reddit.com{permalink}" if permalink else "No Link"

            result_lines.append(f'{i + 1}. "{title}" by u/{author} (Score: {score})')
            result_lines.append(f"   Link: {full_url}")
        return "\n".join(result_lines)

    def search_subreddits(
        self, query: str, limit: int = 5, sort: str = "relevance"
    ) -> str:
        """
        Searches Reddit for subreddits matching a given query string and returns a formatted list of results including subreddit names, subscriber counts, and descriptions.

        Args:
            query: The text to search for in subreddit names and descriptions
            limit: The maximum number of subreddits to return, between 1 and 100 (default: 5)
            sort: The order of results, either 'relevance' or 'activity' (default: 'relevance')

        Returns:
            A formatted string containing a list of matching subreddits with their names, subscriber counts, and descriptions, or an error message if the search fails or parameters are invalid

        Raises:
            RequestException: When the HTTP request to Reddit's API fails
            JSONDecodeError: When the API response contains invalid JSON

        Tags:
            search, important, reddit, api, query, format, list, validation
        """
        valid_sorts = ["relevance", "activity"]
        if sort not in valid_sorts:
            return f"Error: Invalid sort option '{sort}'. Please use one of: {', '.join(valid_sorts)}"
        if not 1 <= limit <= 100:
            return (
                f"Error: Invalid limit '{limit}'. Please use a value between 1 and 100."
            )
        url = f"{self.base_api_url}/subreddits/search"
        params = {
            "q": query,
            "limit": limit,
            "sort": sort,
            # Optionally include NSFW results? Defaulting to false for safety.
            # "include_over_18": "false"
        }
        logger.info(
            f"Searching for subreddits matching '{query}' (limit: {limit}, sort: {sort})"
        )
        response = self._get(url, params=params)
        data = response.json()
        if "error" in data:
            logger.error(
                f"Reddit API error during subreddit search: {data['error']} - {data.get('message', '')}"
            )
            return f"Error from Reddit API during search: {data['error']} - {data.get('message', '')}"
        subreddits = data.get("data", {}).get("children", [])
        if not subreddits:
            return f"No subreddits found matching the query '{query}'."
        result_lines = [
            f"Found {len(subreddits)} subreddits matching '{query}' (sorted by {sort}):\n"
        ]
        for i, sub_container in enumerate(subreddits):
            sub_data = sub_container.get("data", {})
            display_name = sub_data.get("display_name", "N/A")  # e.g., 'python'
            title = sub_data.get(
                "title", "No Title"
            )  # Often the same as display_name or slightly longer
            subscribers = sub_data.get("subscribers", 0)
            # Use public_description if available, fallback to title
            description = sub_data.get("public_description", "").strip() or title

            # Format subscriber count nicely
            subscriber_str = f"{subscribers:,}" if subscribers else "Unknown"

            result_lines.append(
                f"{i + 1}. r/{display_name} ({subscriber_str} subscribers)"
            )
            if description:
                result_lines.append(f"   Description: {description}")
        return "\n".join(result_lines)

    def get_post_flairs(self, subreddit: str):
        """
        Retrieves a list of available post flairs for a specified subreddit using the Reddit API.

        Args:
            subreddit: The name of the subreddit (e.g., 'python', 'worldnews') without the 'r/' prefix

        Returns:
            A list of dictionaries containing flair details if flairs exist, or a string message indicating no flairs are available

        Raises:
            RequestException: When the API request fails or network connectivity issues occur
            JSONDecodeError: When the API response contains invalid JSON data

        Tags:
            fetch, get, reddit, flair, api, read-only
        """
        url = f"{self.base_api_url}/r/{subreddit}/api/link_flair_v2"
        logger.info(f"Fetching post flairs for subreddit: r/{subreddit}")
        response = self._get(url)
        flairs = response.json()
        if not flairs:
            return f"No post flairs available for r/{subreddit}."
        return flairs

    def create_post(
        self,
        subreddit: str,
        title: str,
        kind: str = "self",
        text: str = None,
        url: str = None,
        flair_id: str = None,
    ):
        """
        Creates a new Reddit post in a specified subreddit with support for text posts, link posts, and image posts

        Args:
            subreddit: The name of the subreddit (e.g., 'python', 'worldnews') without the 'r/'
            title: The title of the post
            kind: The type of post; either 'self' (text post) or 'link' (link or image post)
            text: The text content of the post; required if kind is 'self'
            url: The URL of the link or image; required if kind is 'link'. Must end with valid image extension for image posts
            flair_id: The ID of the flair to assign to the post

        Returns:
            The JSON response from the Reddit API, or an error message as a string if the API returns an error

        Raises:
            ValueError: Raised when kind is invalid or when required parameters (text for self posts, url for link posts) are missing

        Tags:
            create, post, social-media, reddit, api, important
        """
        if kind not in ["self", "link"]:
            raise ValueError("Invalid post kind. Must be one of 'self' or 'link'.")
        if kind == "self" and not text:
            raise ValueError("Text content is required for text posts.")
        if kind == "link" and not url:
            raise ValueError("URL is required for link posts (including images).")
        data = {
            "sr": subreddit,
            "title": title,
            "kind": kind,
            "text": text,
            "url": url,
            "flair_id": flair_id,
        }
        data = {k: v for k, v in data.items() if v is not None}
        url_api = f"{self.base_api_url}/api/submit"
        logger.info(f"Submitting a new post to r/{subreddit}")
        response = self._post(url_api, data=data)
        response_json = response.json()
        if (
            response_json
            and "json" in response_json
            and "errors" in response_json["json"]
        ):
            errors = response_json["json"]["errors"]
            if errors:
                error_message = ", ".join(
                    [f"{code}: {message}" for code, message in errors]
                )
                return f"Reddit API error: {error_message}"
        return response_json

    def get_comment_by_id(self, comment_id: str) -> dict:
        """
        Retrieves a specific Reddit comment using its unique identifier.

        Args:
            comment_id: The full unique identifier of the comment (prefixed with 't1_', e.g., 't1_abcdef')

        Returns:
            A dictionary containing the comment data including attributes like author, body, score, etc. If the comment is not found, returns a dictionary with an error message.

        Raises:
            HTTPError: When the Reddit API request fails due to network issues or invalid authentication
            JSONDecodeError: When the API response cannot be parsed as valid JSON

        Tags:
            retrieve, get, reddit, comment, api, fetch, single-item, important
        """
        url = f"https://oauth.reddit.com/api/info.json?id={comment_id}"
        response = self._get(url)
        data = response.json()
        comments = data.get("data", {}).get("children", [])
        if comments:
            return comments[0]["data"]
        else:
            return {"error": "Comment not found."}

    def post_comment(self, parent_id: str, text: str) -> dict:
        """
        Posts a comment to a Reddit post or comment using the Reddit API

        Args:
            parent_id: The full ID of the parent comment or post (e.g., 't3_abc123' for a post, 't1_def456' for a comment)
            text: The text content of the comment to be posted

        Returns:
            A dictionary containing the Reddit API response with details about the posted comment

        Raises:
            RequestException: If the API request fails or returns an error status code
            JSONDecodeError: If the API response cannot be parsed as JSON

        Tags:
            post, comment, social, reddit, api, important
        """
        url = f"{self.base_api_url}/api/comment"
        data = {
            "parent": parent_id,
            "text": text,
        }
        logger.info(f"Posting comment to {parent_id}")
        response = self._post(url, data=data)
        return response.json()

    def edit_content(self, content_id: str, text: str) -> dict:
        """
        Edits the text content of an existing Reddit post or comment using the Reddit API

        Args:
            content_id: The full ID of the content to edit (e.g., 't3_abc123' for a post, 't1_def456' for a comment)
            text: The new text content to replace the existing content

        Returns:
            A dictionary containing the API response with details about the edited content

        Raises:
            RequestException: When the API request fails or network connectivity issues occur
            ValueError: When invalid content_id format or empty text is provided

        Tags:
            edit, update, content, reddit, api, important
        """
        url = f"{self.base_api_url}/api/editusertext"
        data = {
            "thing_id": content_id,
            "text": text,
        }
        logger.info(f"Editing content {content_id}")
        response = self._post(url, data=data)
        return response.json()

    def delete_content(self, content_id: str) -> dict:
        """
        Deletes a specified Reddit post or comment using the Reddit API.

        Args:
            content_id: The full ID of the content to delete (e.g., 't3_abc123' for a post, 't1_def456' for a comment)

        Returns:
            A dictionary containing a success message with the deleted content ID

        Raises:
            HTTPError: When the API request fails or returns an error status code
            RequestException: When there are network connectivity issues or API communication problems

        Tags:
            delete, content-management, api, reddit, important
        """
        url = f"{self.base_api_url}/api/del"
        data = {
            "id": content_id,
        }
        logger.info(f"Deleting content {content_id}")
        response = self._post(url, data=data)
        response.raise_for_status()
        return {"message": f"Content {content_id} deleted successfully."}

    def api_v1_me(self) -> Any:
        """
        Get the current user's information.
        Returns:
            Any: API response data.

        Tags:
            users
        """
        url = f"{self.base_url}/api/v1/me"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_me_karma(self) -> Any:
        """
        Get the current user's karma.

        Returns:
            Any: API response data.

        Tags:
            account
        """
        url = f"{self.base_url}/api/v1/me/karma"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_me_prefs(self) -> Any:
        """
        Get the current user's preferences.

        Returns:
            Any: API response data.

        Tags:
            account
        """
        url = f"{self.base_url}/api/v1/me/prefs"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_me_prefs1(self, accept_pms=None, activity_relevant_ads=None, allow_clicktracking=None, bad_comment_autocollapse=None, beta=None, clickgadget=None, collapse_read_messages=None, compress=None, country_code=None, creddit_autorenew=None, default_comment_sort=None, domain_details=None, email_chat_request=None, email_comment_reply=None, email_community_discovery=None, email_digests=None, email_messages=None, email_new_user_welcome=None, email_post_reply=None, email_private_message=None, email_unsubscribe_all=None, email_upvote_comment=None, email_upvote_post=None, email_user_new_follower=None, email_username_mention=None, enable_default_themes=None, enable_followers=None, feed_recommendations_enabled=None, g=None, hide_ads=None, hide_downs=None, hide_from_robots=None, hide_ups=None, highlight_controversial=None, highlight_new_comments=None, ignore_suggested_sort=None, in_redesign_beta=None, label_nsfw=None, lang=None, legacy_search=None, live_bar_recommendations_enabled=None, live_orangereds=None, mark_messages_read=None, media=None, media_preview=None, min_comment_score=None, min_link_score=None, monitor_mentions=None, newwindow=None, nightmode=None, no_profanity=None, num_comments=None, numsites=None, organic=None, other_theme=None, over_18=None, private_feeds=None, profile_opt_out=None, public_votes=None, research=None, search_include_over_18=None, send_crosspost_messages=None, send_welcome_messages=None, show_flair=None, show_gold_expiration=None, show_link_flair=None, show_location_based_recommendations=None, show_presence=None, show_promote=None, show_stylesheets=None, show_trending=None, show_twitter=None, sms_notifications_enabled=None, store_visits=None, survey_last_seen_time=None, theme_selector=None, third_party_data_personalized_ads=None, third_party_personalized_ads=None, third_party_site_data_personalized_ads=None, third_party_site_data_personalized_content=None, threaded_messages=None, threaded_modmail=None, top_karma_subreddits=None, use_global_defaults=None, video_autoplay=None, whatsapp_comment_reply=None, whatsapp_enabled=None) -> Any:
        """
        Update the current user's preferences.

        Args:
            accept_pms (string): accept_pms Example: 'whitelisted'.
            activity_relevant_ads (boolean): activity_relevant_ads Example: 'False'.
            allow_clicktracking (boolean): allow_clicktracking Example: 'False'.
            bad_comment_autocollapse (string): bad_comment_autocollapse Example: 'off'.
            beta (boolean): beta Example: 'False'.
            clickgadget (boolean): clickgadget Example: 'True'.
            collapse_read_messages (boolean): collapse_read_messages Example: 'False'.
            compress (boolean): compress Example: 'False'.
            country_code (string): country_code Example: 'ZZ'.
            creddit_autorenew (boolean): creddit_autorenew Example: 'False'.
            default_comment_sort (string): default_comment_sort Example: 'new'.
            domain_details (boolean): domain_details Example: 'False'.
            email_chat_request (boolean): email_chat_request Example: 'False'.
            email_comment_reply (boolean): email_comment_reply Example: 'False'.
            email_community_discovery (boolean): email_community_discovery Example: 'False'.
            email_digests (boolean): email_digests Example: 'False'.
            email_messages (boolean): email_messages Example: 'False'.
            email_new_user_welcome (boolean): email_new_user_welcome Example: 'False'.
            email_post_reply (boolean): email_post_reply Example: 'False'.
            email_private_message (boolean): email_private_message Example: 'False'.
            email_unsubscribe_all (boolean): email_unsubscribe_all Example: 'True'.
            email_upvote_comment (boolean): email_upvote_comment Example: 'False'.
            email_upvote_post (boolean): email_upvote_post Example: 'False'.
            email_user_new_follower (boolean): email_user_new_follower Example: 'False'.
            email_username_mention (boolean): email_username_mention Example: 'False'.
            enable_default_themes (boolean): enable_default_themes Example: 'False'.
            enable_followers (boolean): enable_followers Example: 'False'.
            feed_recommendations_enabled (boolean): feed_recommendations_enabled Example: 'False'.
            g (string): g
            hide_ads (boolean): hide_ads Example: 'True'.
            hide_downs (boolean): hide_downs Example: 'False'.
            hide_from_robots (boolean): hide_from_robots Example: 'True'.
            hide_ups (boolean): hide_ups Example: 'False'.
            highlight_controversial (boolean): highlight_controversial Example: 'False'.
            highlight_new_comments (boolean): highlight_new_comments Example: 'True'.
            ignore_suggested_sort (boolean): ignore_suggested_sort Example: 'True'.
            in_redesign_beta (boolean): in_redesign_beta Example: 'True'.
            label_nsfw (boolean): label_nsfw Example: 'True'.
            lang (string): lang Example: 'en'.
            legacy_search (boolean): legacy_search Example: 'False'.
            live_bar_recommendations_enabled (boolean): live_bar_recommendations_enabled Example: 'False'.
            live_orangereds (boolean): live_orangereds Example: 'False'.
            mark_messages_read (boolean): mark_messages_read Example: 'True'.
            media (string): media Example: 'subreddit'.
            media_preview (string): media_preview Example: 'subreddit'.
            min_comment_score (number): min_comment_score Example: '-100'.
            min_link_score (number): min_link_score Example: '-100'.
            monitor_mentions (boolean): monitor_mentions Example: 'True'.
            newwindow (boolean): newwindow Example: 'False'.
            nightmode (boolean): nightmode Example: 'True'.
            no_profanity (boolean): no_profanity Example: 'False'.
            num_comments (number): num_comments Example: '500'.
            numsites (number): numsites Example: '100'.
            organic (string): organic
            other_theme (string): other_theme
            over_18 (boolean): over_18 Example: 'True'.
            private_feeds (boolean): private_feeds Example: 'True'.
            profile_opt_out (boolean): profile_opt_out Example: 'False'.
            public_votes (boolean): public_votes Example: 'False'.
            research (boolean): research Example: 'False'.
            search_include_over_18 (boolean): search_include_over_18 Example: 'True'.
            send_crosspost_messages (boolean): send_crosspost_messages Example: 'True'.
            send_welcome_messages (boolean): send_welcome_messages Example: 'True'.
            show_flair (boolean): show_flair Example: 'True'.
            show_gold_expiration (boolean): show_gold_expiration Example: 'True'.
            show_link_flair (boolean): show_link_flair Example: 'True'.
            show_location_based_recommendations (boolean): show_location_based_recommendations Example: 'False'.
            show_presence (boolean): show_presence Example: 'False'.
            show_promote (boolean): show_promote Example: 'False'.
            show_stylesheets (boolean): show_stylesheets Example: 'True'.
            show_trending (boolean): show_trending Example: 'False'.
            show_twitter (boolean): show_twitter Example: 'False'.
            sms_notifications_enabled (boolean): sms_notifications_enabled Example: 'False'.
            store_visits (boolean): store_visits Example: 'False'.
            survey_last_seen_time (string): survey_last_seen_time
            theme_selector (string): theme_selector
            third_party_data_personalized_ads (boolean): third_party_data_personalized_ads Example: 'False'.
            third_party_personalized_ads (boolean): third_party_personalized_ads Example: 'False'.
            third_party_site_data_personalized_ads (boolean): third_party_site_data_personalized_ads Example: 'False'.
            third_party_site_data_personalized_content (boolean): third_party_site_data_personalized_content Example: 'False'.
            threaded_messages (boolean): threaded_messages Example: 'True'.
            threaded_modmail (boolean): threaded_modmail Example: 'True'.
            top_karma_subreddits (boolean): top_karma_subreddits Example: 'False'.
            use_global_defaults (boolean): use_global_defaults Example: 'False'.
            video_autoplay (boolean): video_autoplay Example: 'False'.
            whatsapp_comment_reply (boolean): whatsapp_comment_reply Example: 'False'.
            whatsapp_enabled (boolean): whatsapp_enabled
                Example:
                ```json
                {
                  "accept_pms": "whitelisted",
                  "activity_relevant_ads": false,
                  "allow_clicktracking": false,
                  "bad_comment_autocollapse": "off",
                  "beta": false,
                  "clickgadget": true,
                  "collapse_read_messages": false,
                  "compress": false,
                  "country_code": "ZZ",
                  "creddit_autorenew": false,
                  "default_comment_sort": "new",
                  "domain_details": false,
                  "email_chat_request": false,
                  "email_comment_reply": false,
                  "email_community_discovery": false,
                  "email_digests": false,
                  "email_messages": false,
                  "email_new_user_welcome": false,
                  "email_post_reply": false,
                  "email_private_message": false,
                  "email_unsubscribe_all": true,
                  "email_upvote_comment": false,
                  "email_upvote_post": false,
                  "email_user_new_follower": false,
                  "email_username_mention": false,
                  "enable_default_themes": false,
                  "enable_followers": false,
                  "feed_recommendations_enabled": false,
                  "g": "",
                  "hide_ads": true,
                  "hide_downs": false,
                  "hide_from_robots": true,
                  "hide_ups": false,
                  "highlight_controversial": false,
                  "highlight_new_comments": true,
                  "ignore_suggested_sort": true,
                  "in_redesign_beta": true,
                  "label_nsfw": true,
                  "lang": "en",
                  "legacy_search": false,
                  "live_bar_recommendations_enabled": false,
                  "live_orangereds": false,
                  "mark_messages_read": true,
                  "media": "subreddit",
                  "media_preview": "subreddit",
                  "min_comment_score": -100,
                  "min_link_score": -100,
                  "monitor_mentions": true,
                  "newwindow": false,
                  "nightmode": true,
                  "no_profanity": false,
                  "num_comments": 500,
                  "numsites": 100,
                  "organic": null,
                  "other_theme": "",
                  "over_18": true,
                  "private_feeds": true,
                  "profile_opt_out": false,
                  "public_votes": false,
                  "research": false,
                  "search_include_over_18": true,
                  "send_crosspost_messages": true,
                  "send_welcome_messages": true,
                  "show_flair": true,
                  "show_gold_expiration": true,
                  "show_link_flair": true,
                  "show_location_based_recommendations": false,
                  "show_presence": false,
                  "show_promote": false,
                  "show_stylesheets": true,
                  "show_trending": false,
                  "show_twitter": false,
                  "sms_notifications_enabled": false,
                  "store_visits": false,
                  "survey_last_seen_time": null,
                  "theme_selector": "",
                  "third_party_data_personalized_ads": false,
                  "third_party_personalized_ads": false,
                  "third_party_site_data_personalized_ads": false,
                  "third_party_site_data_personalized_content": false,
                  "threaded_messages": true,
                  "threaded_modmail": true,
                  "top_karma_subreddits": false,
                  "use_global_defaults": false,
                  "video_autoplay": false,
                  "whatsapp_comment_reply": false,
                  "whatsapp_enabled": false
                }
                ```

        Returns:
            Any: API response data.

        Tags:
            account
        """
        request_body = {
            'accept_pms': accept_pms,
            'activity_relevant_ads': activity_relevant_ads,
            'allow_clicktracking': allow_clicktracking,
            'bad_comment_autocollapse': bad_comment_autocollapse,
            'beta': beta,
            'clickgadget': clickgadget,
            'collapse_read_messages': collapse_read_messages,
            'compress': compress,
            'country_code': country_code,
            'creddit_autorenew': creddit_autorenew,
            'default_comment_sort': default_comment_sort,
            'domain_details': domain_details,
            'email_chat_request': email_chat_request,
            'email_comment_reply': email_comment_reply,
            'email_community_discovery': email_community_discovery,
            'email_digests': email_digests,
            'email_messages': email_messages,
            'email_new_user_welcome': email_new_user_welcome,
            'email_post_reply': email_post_reply,
            'email_private_message': email_private_message,
            'email_unsubscribe_all': email_unsubscribe_all,
            'email_upvote_comment': email_upvote_comment,
            'email_upvote_post': email_upvote_post,
            'email_user_new_follower': email_user_new_follower,
            'email_username_mention': email_username_mention,
            'enable_default_themes': enable_default_themes,
            'enable_followers': enable_followers,
            'feed_recommendations_enabled': feed_recommendations_enabled,
            'g': g,
            'hide_ads': hide_ads,
            'hide_downs': hide_downs,
            'hide_from_robots': hide_from_robots,
            'hide_ups': hide_ups,
            'highlight_controversial': highlight_controversial,
            'highlight_new_comments': highlight_new_comments,
            'ignore_suggested_sort': ignore_suggested_sort,
            'in_redesign_beta': in_redesign_beta,
            'label_nsfw': label_nsfw,
            'lang': lang,
            'legacy_search': legacy_search,
            'live_bar_recommendations_enabled': live_bar_recommendations_enabled,
            'live_orangereds': live_orangereds,
            'mark_messages_read': mark_messages_read,
            'media': media,
            'media_preview': media_preview,
            'min_comment_score': min_comment_score,
            'min_link_score': min_link_score,
            'monitor_mentions': monitor_mentions,
            'newwindow': newwindow,
            'nightmode': nightmode,
            'no_profanity': no_profanity,
            'num_comments': num_comments,
            'numsites': numsites,
            'organic': organic,
            'other_theme': other_theme,
            'over_18': over_18,
            'private_feeds': private_feeds,
            'profile_opt_out': profile_opt_out,
            'public_votes': public_votes,
            'research': research,
            'search_include_over_18': search_include_over_18,
            'send_crosspost_messages': send_crosspost_messages,
            'send_welcome_messages': send_welcome_messages,
            'show_flair': show_flair,
            'show_gold_expiration': show_gold_expiration,
            'show_link_flair': show_link_flair,
            'show_location_based_recommendations': show_location_based_recommendations,
            'show_presence': show_presence,
            'show_promote': show_promote,
            'show_stylesheets': show_stylesheets,
            'show_trending': show_trending,
            'show_twitter': show_twitter,
            'sms_notifications_enabled': sms_notifications_enabled,
            'store_visits': store_visits,
            'survey_last_seen_time': survey_last_seen_time,
            'theme_selector': theme_selector,
            'third_party_data_personalized_ads': third_party_data_personalized_ads,
            'third_party_personalized_ads': third_party_personalized_ads,
            'third_party_site_data_personalized_ads': third_party_site_data_personalized_ads,
            'third_party_site_data_personalized_content': third_party_site_data_personalized_content,
            'threaded_messages': threaded_messages,
            'threaded_modmail': threaded_modmail,
            'top_karma_subreddits': top_karma_subreddits,
            'use_global_defaults': use_global_defaults,
            'video_autoplay': video_autoplay,
            'whatsapp_comment_reply': whatsapp_comment_reply,
            'whatsapp_enabled': whatsapp_enabled,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/api/v1/me/prefs"
        query_params = {}
        response = self._patch(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_me_trophies(self) -> Any:
        """
        Get the current user's trophies.

        Returns:
            Any: API response data.

        Tags:
            account
        """
        url = f"{self.base_url}/api/v1/me/trophies"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def prefs_friends(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's friends.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            account
        """
        url = f"{self.base_url}/prefs/friends"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def prefs_blocked(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's blocked users.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            account
        """
        url = f"{self.base_url}/prefs/blocked"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def prefs_messaging(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's messaging preferences.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            account
        """
        url = f"{self.base_url}/prefs/messaging"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def prefs_trusted(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's trusted users.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            account
        """
        url = f"{self.base_url}/prefs/trusted"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_needs_captcha(self) -> Any:
        """
        Check if the current user needs a captcha.

        Returns:
            Any: API response data.

        Tags:
            captcha
        """
        url = f"{self.base_url}/api/needs_captcha"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_collections_collection(self, collection_id=None, include_links=None) -> Any:
        """
        Get a collection by ID.

        Args:
            collection_id (string): the UUID of a collection
            include_links (string): boolean value(true, false)

        Returns:
            Any: API response data.

        Tags:
            collections
        """
        url = f"{self.base_url}/api/v1/collections/collection"
        query_params = {k: v for k, v in [('collection_id', collection_id), ('include_links', include_links)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_collections_subreddit_collections(self) -> Any:
        """
        Get the current user's subreddit collections.

        Returns:
            Any: API response data.

        Tags:
            collections
        """
        url = f"{self.base_url}/api/v1/collections/subreddit_collections"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_subreddit_emoji_emoji_name(self, subreddit, emoji_name) -> Any:
        """
        Get an emoji by name.

        Args:
            subreddit (string): subreddit
            emoji_name (string): emoji_name

        Returns:
            Any: API response data.

        Tags:
            emoji
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if emoji_name is None:
            raise ValueError("Missing required parameter 'emoji_name'")
        url = f"{self.base_url}/api/v1/{subreddit}/emoji/{emoji_name}"
        query_params = {}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_subreddit_emojis_all(self, subreddit) -> Any:
        """
        Get all emojis for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            emoji
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/api/v1/{subreddit}/emojis/all"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_flair(self, subreddit) -> Any:
        """
        Get the current user's flair for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            flair
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/flair"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()


    def r_subreddit_api_flairlist(self, subreddit, after=None, before=None, count=None, limit=None, name=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's flair list for a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 1000)
            name (string): a user by name
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            flair
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/flairlist"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('name', name), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_link_flair(self, subreddit) -> Any:
        """
        Get the current user's link flair for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            flair
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/link_flair"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_link_flair_v2(self, subreddit) -> Any:
        """
        Get the current user's link flair for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            flair
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/link_flair_v2"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_user_flair(self, subreddit) -> Any:
        """
        Get the current user's user flair for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            flair
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/user_flair"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_user_flair_v2(self, subreddit) -> Any:
        """
        Get the current user's user flair for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            flair
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/user_flair_v2"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_info(self, id=None, sr_name=None, url=None) -> Any:
        """
        Get information about a link or comment.

        Args:
            id (string): A comma-separated list of thing fullnames
            sr_name (string): A comma-separated list of subreddit names
            url (string): a valid URL

        Returns:
            Any: API response data.

        Tags:
            links & comments
        """
        url = f"{self.base_url}/api/info"
        query_params = {k: v for k, v in [('id', id), ('sr_name', sr_name), ('url', url)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_info(self, subreddit, id=None, sr_name=None, url=None) -> Any:
        """
        Get information about a link or comment in a subreddit.

        Args:
            subreddit (string): subreddit
            id (string): A comma-separated list of thing fullnames
            sr_name (string): A comma-separated list of subreddit names
            url (string): a valid URL

        Returns:
            Any: API response data.

        Tags:
            links & comments
        """ 
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/{subreddit}/api/info"
        query_params = {k: v for k, v in [('id', id), ('sr_name', sr_name), ('url', url)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_morechildren(self, api_type=None, children=None, depth=None, id=None, limit_children=None, link_id=None, sort=None) -> Any:
        """
        Get more children for a link or comment.

        Args:
            api_type (string): the string "json" Example: 'json'.
            children (string): No description provided.
            depth (string): (optional) an integer
            id (string): (optional) id of the associated MoreChildren object
            limit_children (string): boolean value (true, false)
            link_id (string): fullname of a link
            sort (string): one of (confidence, top, new, controversial, old, random, qa, live)

        Returns:
            Any: API response data.

        Tags:
            links & comments
        """
        url = f"{self.base_url}/api/morechildren"
        query_params = {k: v for k, v in [('api_type', api_type), ('children', children), ('depth', depth), ('id', id), ('limit_children', limit_children), ('link_id', link_id), ('sort', sort)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_saved_categories(self) -> Any:
        """
        Get the current user's saved categories.

        Returns:
            Any: API response data.

        Tags:
            links & comments
        """
        url = f"{self.base_url}/api/saved_categories"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def req(self) -> Any:
        """
        Get the current user's requests.

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/req"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def best(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the best posts.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string all
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/best"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def by_id_names(self, names) -> Any:
        """
        Get posts by ID.

        Args:
            names (string): names

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if names is None:
            raise ValueError("Missing required parameter 'names'")
        url = f"{self.base_url}/by_id/{names}"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def comments_article(self, article, comment=None, context=None, depth=None, limit=None, showedits=None, showmedia=None, showmore=None, showtitle=None, sort=None, sr_detail=None, theme=None, threaded=None, truncate=None) -> Any:
        """
        Get comments for a post.

        Args:
            article (string): article
            comment (string): (optional) ID36 of a comment
            context (string): an integer between 0 and 8
            depth (string): (optional) an integer
            limit (string): (optional) an integer
            showedits (string): boolean value (true, false)
            showmedia (string): boolean value (true, false)
            showmore (string): boolean value (true, false)
            showtitle (string): boolean value (true, false)
            sort (string): one of (confidence, top, new, controversial, old, random, qa, live)
            sr_detail (string): (optional) expand subreddits
            theme (string): one of (default, dark)
            threaded (string): boolean value (true, false)
            truncate (string): an integer between 0 and 50

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if article is None:
            raise ValueError("Missing required parameter 'article'")
        url = f"{self.base_url}/comments/{article}"
        query_params = {k: v for k, v in [('comment', comment), ('context', context), ('depth', depth), ('limit', limit), ('showedits', showedits), ('showmedia', showmedia), ('showmore', showmore), ('showtitle', showtitle), ('sort', sort), ('sr_detail', sr_detail), ('theme', theme), ('threaded', threaded), ('truncate', truncate)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_post_comments_details(self, post_id: str) -> Any:
        """
        Get post details and comments like title, author, score, etc.

        Args:
            post_id (string): The Reddit post ID ( e.g. '1m734tx' for https://www.reddit.com/r/mcp/comments/1m734tx/comment/n4occ77/)

        Returns:
            Any: API response data containing post details and comments.

        Tags:
            listings, comments, posts, important
        """
        
        
        url = f"{self.base_url}/comments/{post_id}.json"
        query_params = {}
        response = self._get(url, params=query_params)
        return self._handle_response(response)



    def controversial(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the most controversial posts.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/controversial"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def duplicates_article(self, article, after=None, before=None, count=None, crossposts_only=None, limit=None, show=None, sort=None, sr=None, sr_detail=None) -> Any:
        """
        Get duplicate posts.

        Args:
            article (string): article
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            crossposts_only (string): boolean value (true, false)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sort (string): one of (num_comments, new)
            sr (string): subreddit name
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if article is None:
            raise ValueError("Missing required parameter 'article'")
        url = f"{self.base_url}/duplicates/{article}"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('crossposts_only', crossposts_only), ('limit', limit), ('show', show), ('sort', sort), ('sr', sr), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def hot(self, g=None, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the hottest posts.

        Args:
            g (string): one of (GLOBAL, US, AR, AU, BG, CA, CL, CO, HR, CZ, FI, FR, DE, GR, HU, IS, IN, IE, IT, JP, MY, MX, NZ, PH, PL, PT, PR, RO, RS, SG, ES, SE, TW, TH, TR, GB, US_WA, US_DE, US_DC, US_WI, US_WV, US_HI, US_FL, US_WY, US_NH, US_NJ, US_NM, US_TX, US_LA, US_NC, US_ND, US_NE, US_TN, US_NY, US_PA, US_CA, US_NV, US_VA, US_CO, US_AK, US_AL, US_AR, US_VT, US_IL, US_GA, US_IN, US_IA, US_OK, US_AZ, US_ID, US_CT, US_ME, US_MD, US_MA, US_OH, US_UT, US_MO, US_MN, US_MI, US_RI, US_KS, US_MT, US_MS, US_SC, US_KY, US_OR, US_SD)
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/hot"
        query_params = {k: v for k, v in [('g', g), ('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def new(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the newest posts.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/new"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_comments_article(self, subreddit, article, comment=None, context=None, depth=None, limit=None, showedits=None, showmedia=None, showmore=None, showtitle=None, sort=None, sr_detail=None, theme=None, threaded=None, truncate=None) -> Any:
        """
        Get comments for a post in a subreddit.

        Args:
            subreddit (string): subreddit
            article (string): article
            comment (string): (optional) ID36 of a comment
            context (string): an integer between 0 and 8
            depth (string): (optional) an integer
            limit (string): (optional) an integer
            showedits (string): boolean value (true, false)
            showmedia (string): boolean value (true, false)
            showmore (string): boolean value (true, false)
            showtitle (string): boolean value (true, false)
            sort (string): one of (confidence, top, new, controversial, old, random, qa, live)
            sr_detail (string): (optional) expand subreddits
            theme (string): one of (default, dark)
            threaded (string): boolean value (true, false)
            truncate (string): an integer between 0 and 50

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if article is None:
            raise ValueError("Missing required parameter 'article'")
        url = f"{self.base_url}/r/{subreddit}/comments/{article}"
        query_params = {k: v for k, v in [('comment', comment), ('context', context), ('depth', depth), ('limit', limit), ('showedits', showedits), ('showmedia', showmedia), ('showmore', showmore), ('showtitle', showtitle), ('sort', sort), ('sr_detail', sr_detail), ('theme', theme), ('threaded', threaded), ('truncate', truncate)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_controversial(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the most controversial posts in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/controversial"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_hot(self, subreddit, g=None, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the hottest posts in a subreddit.

        Args:
            subreddit (string): subreddit
            g (string): one of (GLOBAL, US, AR, AU, BG, CA, CL, CO, HR, CZ, FI, FR, DE, GR, HU, IS, IN, IE, IT, JP, MY, MX, NZ, PH, PL, PT, PR, RO, RS, SG, ES, SE, TW, TH, TR, GB, US_WA, US_DE, US_DC, US_WI, US_WV, US_HI, US_FL, US_WY, US_NH, US_NJ, US_NM, US_TX, US_LA, US_NC, US_ND, US_NE, US_TN, US_NY, US_PA, US_CA, US_NV, US_VA, US_CO, US_AK, US_AL, US_AR, US_VT, US_IL, US_GA, US_IN, US_IA, US_OK, US_AZ, US_ID, US_CT, US_ME, US_MD, US_MA, US_OH, US_UT, US_MO, US_MN, US_MI, US_RI, US_KS, US_MT, US_MS, US_SC, US_KY, US_OR, US_SD)
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/hot"
        query_params = {k: v for k, v in [('g', g), ('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_new(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the newest posts in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/new"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_random(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get a random post in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/random"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_rising(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the rising posts in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/rising"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_top(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the top posts in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/top"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def random(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get a random post.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/random"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def rising(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the rising posts.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/rising"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def top(self, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the top posts.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            listings
        """
        url = f"{self.base_url}/top"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_saved_media_text(self, url=None) -> Any:
        """
        Get the text of a saved media.

        Args:
            url (string): a valid URL

        Returns:
            Any: API response data.

        Tags:
            misc
        """
        url = f"{self.base_url}/api/saved_media_text"
        query_params = {k: v for k, v in [('url', url)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_scopes(self, scopes=None) -> Any:
        """
        Get the current user's scopes.

        Args:
            scopes (string): (optional) An OAuth2 scope string

        Returns:
            Any: API response data.

        Tags:
            misc
        """
        url = f"{self.base_url}/api/v1/scopes"
        query_params = {k: v for k, v in [('scopes', scopes)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_saved_media_text(self, subreddit, url=None) -> Any:
        """
        Get the text of a saved media in a subreddit.

        Args:
            subreddit (string): subreddit
            url (string): a valid URL

        Returns:
            Any: API response data.

        Tags:
            misc
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/saved_media_text"
        query_params = {k: v for k, v in [('url', url)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_log(self, subreddit, after=None, before=None, count=None, limit=None, mod=None, show=None, sr_detail=None, type=None) -> Any:
        """
        Get the log of a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): a ModAction ID
            before (string): a ModAction ID
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 500)
            mod (string): (optional) a moderator filter
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits
            type (string): one of (banuser, unbanuser, spamlink, removelink, approvelink, spamcomment, removecomment, approvecomment, addmoderator, showcomment, invitemoderator, uninvitemoderator, acceptmoderatorinvite, removemoderator, addcontributor, removecontributor, editsettings, editflair, distinguish, marknsfw, wikibanned, wikicontributor, wikiunbanned, wikipagelisted, removewikicontributor, wikirevise, wikipermlevel, ignorereports, unignorereports, setpermissions, setsuggestedsort, sticky, unsticky, setcontestmode, unsetcontestmode, lock, unlock, muteuser, unmuteuser, createrule, editrule, reorderrules, deleterule, spoiler, unspoiler, modmail_enrollment, community_styling, community_widgets, markoriginalcontent, collections, events, hidden_award, add_community_topics, remove_community_topics, create_scheduled_post, edit_scheduled_post, delete_scheduled_post, submit_scheduled_post, edit_post_requirements, invitesubscriber, submit_content_rating_survey, adjust_post_crowd_control_level, enable_post_crowd_control_filter, disable_post_crowd_control_filter, deleteoverriddenclassification, overrideclassification, reordermoderators, snoozereports, unsnoozereports, addnote, deletenote, addremovalreason, createremovalreason, updateremovalreason, deleteremovalreason, reorderremovalreason, dev_platform_app_changed, dev_platform_app_disabled, dev_platform_app_enabled, dev_platform_app_installed, dev_platform_app_uninstalled)

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/log"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('mod', mod), ('show', show), ('sr_detail', sr_detail), ('type', type)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_edited(self, subreddit, after=None, before=None, count=None, limit=None, location=None, only=None, show=None, sr_detail=None) -> Any:
        """
        Get the edited posts in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            location (string): No description provided.
            only (string): one of (links, comments, chat_comments)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/edited"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('location', location), ('only', only), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_modqueue(self, subreddit, after=None, before=None, count=None, limit=None, location=None, only=None, show=None, sr_detail=None) -> Any:
        """
        Get the modqueue in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            location (string): No description provided.
            only (string): one of (links, comments, chat_comments)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/modqueue"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('location', location), ('only', only), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_reports(self, subreddit, after=None, before=None, count=None, limit=None, location=None, only=None, show=None, sr_detail=None) -> Any:
        """
        Get the reports in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            location (string): No description provided.
            only (string): one of (links, comments, chat_comments)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/reports"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('location', location), ('only', only), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_spam(self, subreddit, after=None, before=None, count=None, limit=None, location=None, only=None, show=None, sr_detail=None) -> Any:
        """
        Get the spam posts in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            location (string): No description provided.
            only (string): one of (links, comments, chat_comments)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/spam"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('location', location), ('only', only), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_unmoderated(self, subreddit, after=None, before=None, count=None, limit=None, location=None, only=None, show=None, sr_detail=None) -> Any:
        """
        Get the unmoderated posts in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            location (string): No description provided.
            only (string): one of (links, comments, chat_comments)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/unmoderated"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('location', location), ('only', only), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_stylesheet(self, subreddit) -> Any:
        """
        Get the stylesheet of a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/stylesheet"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def stylesheet(self) -> Any:
        """
        Get the stylesheet of the current user.

        Returns:
            Any: API response data.

        Tags:
            moderation
        """
        url = f"{self.base_url}/stylesheet"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_notes1(self, before=None, filter=None, limit=None, subreddit=None, user=None) -> Any:
        """
        Get the mod notes of a subreddit.

        Args:
            before (string): (optional) an encoded string used for pagination with mod notes
            filter (string): (optional) one of (NOTE, APPROVAL, REMOVAL, BAN, MUTE, INVITE, SPAM, CONTENT_CHANGE, MOD_ACTION, ALL), to be used for querying specific types of mod notes (default: all)
            limit (string): (optional) the number of mod notes to return in the response payload (default: 25, max: 100)
            subreddit (string): subreddit name
            user (string): account username

        Returns:
            Any: API response data.

        Tags:
            modnote
        """
        url = f"{self.base_url}/api/mod/notes"
        query_params = {k: v for k, v in [('before', before), ('filter', filter), ('limit', limit), ('subreddit', subreddit), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_notes(self, note_id=None, subreddit=None, user=None) -> Any:
        """
        Delete a mod note.

        Args:
            note_id (string): a unique ID for the note to be deleted (should have a ModNote_ prefix)
            subreddit (string): subreddit name
            user (string): account username

        Returns:
            Any: API response data.

        Tags:
            modnote
        """
        url = f"{self.base_url}/api/mod/notes"
        query_params = {k: v for k, v in [('note_id', note_id), ('subreddit', subreddit), ('user', user)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_notes_recent(self, before=None, filter=None, limit=None, subreddits=None, user=None) -> Any:
        """
        Get the recent mod notes.

        Args:
            before (string): (optional) an encoded string used for pagination with mod notes
            filter (string): (optional) one of (NOTE, APPROVAL, REMOVAL, BAN, MUTE, INVITE, SPAM, CONTENT_CHANGE, MOD_ACTION, ALL), to be used for querying specific types of mod notes (default: all)
            limit (string): (optional) the number of mod notes to return in the response payload (default: 25, max: 100)
            subreddits (string): a comma-separated list of subreddits by name
            user (string): a comma-separated list of usernames

        Returns:
            Any: API response data.

        Tags:
            modnote
        """
        url = f"{self.base_url}/api/mod/notes/recent"
        query_params = {k: v for k, v in [('before', before), ('filter', filter), ('limit', limit), ('subreddits', subreddits), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_multi_mine(self, expand_srs=None) -> Any:
        """
        Get the current user's multi.

        Args:
            expand_srs (string): boolean value (true, false)

        Returns:
            Any: API response data.

        Tags:
            multis
        """
        url = f"{self.base_url}/api/multi/mine"
        query_params = {k: v for k, v in [('expand_srs', expand_srs)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_multi_user_username(self, username, expand_srs=None) -> Any:
        """
        Get a user's multi.

        Args:
            username (string): username
            expand_srs (string): boolean value (true, false)

        Returns:
            Any: API response data.

        Tags:
            multis
        """
        if username is None:
            raise ValueError("Missing required parameter 'username'")
        url = f"{self.base_url}/api/multi/user/{username}"
        query_params = {k: v for k, v in [('expand_srs', expand_srs)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_multi_multipath1(self, multipath, expand_srs=None) -> Any:
        """
        Get a multi.

        Args:
            multipath (string): multipath
            expand_srs (string): boolean value (true, false)

        Returns:
            Any: API response data.

        Tags:
            multis
        """
        if multipath is None:
            raise ValueError("Missing required parameter 'multipath'")
        url = f"{self.base_url}/api/multi/{multipath}"
        query_params = {k: v for k, v in [('expand_srs', expand_srs)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_multi_multipath(self, multipath, expand_srs=None) -> Any:
        """
        Delete a multi.

        Args:
            multipath (string): multipath
            expand_srs (string): boolean value (true, false)

        Returns:
            Any: API response data.

        Tags:
            multis
        """
        if multipath is None:
            raise ValueError("Missing required parameter 'multipath'")
        url = f"{self.base_url}/api/multi/{multipath}"
        query_params = {k: v for k, v in [('expand_srs', expand_srs)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_multi_multipath_description(self, multipath) -> Any:
        """
        Get a multi's description.

        Args:
            multipath (string): multipath

        Returns:
            Any: API response data.

        Tags:
            multis
        """
        if multipath is None:
            raise ValueError("Missing required parameter 'multipath'")
        url = f"{self.base_url}/api/multi/{multipath}/description"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_multi_multipath_rsubreddit1(self, multipath, subreddit) -> Any:
        """
        Get a multi's subreddit.

        Args:
            multipath (string): multipath
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            multis
        """
        if multipath is None:
            raise ValueError("Missing required parameter 'multipath'")
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/api/multi/{multipath}/r/{subreddit}"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_multi_multipath_rsubreddit(self, multipath, subreddit) -> Any:
        """
        Delete a multi's subreddit.

        Args:
            multipath (string): multipath
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            multis
        """
        if multipath is None:
            raise ValueError("Missing required parameter 'multipath'")
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/api/multi/{multipath}/r/{subreddit}"
        query_params = {}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations(self, after=None, entity=None, limit=None, sort=None, state=None) -> Any:
        """
        Get the mod conversations.

        Args:
            after (string): A ModMail Converstion ID, in the form ModmailConversation_<id>
            entity (string): A comma-separated list of subreddit names
            limit (string): an integer between 1 and 100 (default: 25)
            sort (string): one of (recent, mod, user, unread)
            state (string): one of (all, appeals, notifications, inbox, filtered, inprogress, mod, archived, default, highlighted, join_requests, new)

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        url = f"{self.base_url}/api/mod/conversations"
        query_params = {k: v for k, v in [('after', after), ('entity', entity), ('limit', limit), ('sort', sort), ('state', state)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_conversation_id(self, conversation_id, markRead=None) -> Any:
        """
        Get a mod conversation.

        Args:
            conversation_id (string): conversation_id
            markRead (string): boolean value (true, false)

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        if conversation_id is None:
            raise ValueError("Missing required parameter 'conversation_id'")
        url = f"{self.base_url}/api/mod/conversations/{conversation_id}"
        query_params = {k: v for k, v in [('markRead', markRead)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_conversation_id_highlight(self, conversation_id) -> Any:
        """
        Highlight a mod conversation.

        Args:
            conversation_id (string): conversation_id

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        if conversation_id is None:
            raise ValueError("Missing required parameter 'conversation_id'")
        url = f"{self.base_url}/api/mod/conversations/{conversation_id}/highlight"
        query_params = {}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_conversation_id_unarchive(self, conversation_id) -> Any:
        """
        Unarchive a mod conversation.

        Args:
            conversation_id (string): conversation_id

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        if conversation_id is None:
            raise ValueError("Missing required parameter 'conversation_id'")
        url = f"{self.base_url}/api/mod/conversations/{conversation_id}/unarchive"
        query_params = {}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_conversation_id_unban(self, conversation_id) -> Any:
        """
        Unban a mod conversation.

        Args:
            conversation_id (string): conversation_id

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        if conversation_id is None:
            raise ValueError("Missing required parameter 'conversation_id'")
        url = f"{self.base_url}/api/mod/conversations/{conversation_id}/unban"
        query_params = {}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_conversation_id_unmute(self, conversation_id) -> Any:
        """
        Unmute a mod conversation.

        Args:
            conversation_id (string): conversation_id

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        if conversation_id is None:
            raise ValueError("Missing required parameter 'conversation_id'")
        url = f"{self.base_url}/api/mod/conversations/{conversation_id}/unmute"
        query_params = {}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_conversation_id_user(self, conversation_id) -> Any:
        """
        Get a mod conversation's user.

        Args:
            conversation_id (string): conversation_id

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        if conversation_id is None:
            raise ValueError("Missing required parameter 'conversation_id'")
        url = f"{self.base_url}/api/mod/conversations/{conversation_id}/user"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_subreddits(self) -> Any:
        """
        Get the mod conversations' subreddits.

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        url = f"{self.base_url}/api/mod/conversations/subreddits"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_mod_conversations_unread_count(self) -> Any:
        """
        Get the unread count of the mod conversations.

        Returns:
            Any: API response data.

        Tags:
            new modmail
        """
        url = f"{self.base_url}/api/mod/conversations/unread/count"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def message_inbox(self, mark=None, mid=None, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's inbox.

        Args:
            mark (string): one of (true, false)
            mid (string): No description provided.
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            private messages
        """
        url = f"{self.base_url}/message/inbox"
        query_params = {k: v for k, v in [('mark', mark), ('mid', mid), ('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def message_sent(self, mark=None, mid=None, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's sent messages.

        Args:
            mark (string): one of (true, false)
            mid (string): No description provided.
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            private messages
        """
        url = f"{self.base_url}/message/sent"
        query_params = {k: v for k, v in [('mark', mark), ('mid', mid), ('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def message_unread(self, mark=None, mid=None, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the current user's unread messages.

        Args:
            mark (string): one of (true, false)
            mid (string): No description provided.
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            private messages
        """
        url = f"{self.base_url}/message/unread"
        query_params = {k: v for k, v in [('mark', mark), ('mid', mid), ('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def search(self, after=None, before=None, category=None, count=None, include_facets=None, limit=None, q=None, restrict_sr=None, show=None, sort=None, sr_detail=None, t=None, type=None) -> Any:
        """
        Search for posts, comments, and users.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            category (string): a string no longer than 5 characters
            count (string): a positive integer (default: 0)
            include_facets (string): boolean value (true, false)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            q (string): a string no longer than 512 characters
            restrict_sr (string): boolean value (true, false)
            show (string): (optional) the string "all" Example: 'all'.
            sort (string): one of (relevance, hot, top, new, comments)
            sr_detail (string): (optional) expand subreddits
            t (string): one of (hour, day, week, month, year, all)
            type (string): (optional) A comma-separated list of result types (sr, link, user)

        Returns:
            Any: API response data.

        Tags:
            search
        """
        url = f"{self.base_url}/search"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('category', category), ('count', count), ('include_facets', include_facets), ('limit', limit), ('q', q), ('restrict_sr', restrict_sr), ('show', show), ('sort', sort), ('sr_detail', sr_detail), ('t', t), ('type', type)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_search(self, subreddit, after=None, before=None, category=None, count=None, include_facets=None, limit=None, q=None, restrict_sr=None, show=None, sort=None, sr_detail=None, t=None, type=None) -> Any:
        """
        Search for posts, comments, and users in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            category (string): a string no longer than 5 characters
            count (string): a positive integer (default: 0)
            include_facets (string): boolean value (true, false)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            q (string): a string no longer than 512 characters
            restrict_sr (string): boolean value (true, false)
            show (string): (optional) the string "all" Example: 'all'.
            sort (string): one of (relevance, hot, top, new, comments)
            sr_detail (string): (optional) expand subreddits
            t (string): one of (hour, day, week, month, year, all)
            type (string): (optional) A comma-separated list of result types (sr, link, user)

        Returns:
            Any: API response data.

        Tags:
            search
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/search"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('category', category), ('count', count), ('include_facets', include_facets), ('limit', limit), ('q', q), ('restrict_sr', restrict_sr), ('show', show), ('sort', sort), ('sr_detail', sr_detail), ('t', t), ('type', type)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()


    def api_search_reddit_names(self, exact=None, include_over_18=None, include_unadvertisable=None, query=None, search_query_id=None, typeahead_active=None) -> Any:
        """
        Search for subreddits.

        Args:
            exact (string): boolean value (true, false) Example: 'false'.
            include_over_18 (string): boolean value (true, false) Example: 'true'.
            include_unadvertisable (string): boolean value (true, false) Example: 'true'.
            query (string): a string up to 50 characters long, consisting of printable characters
            search_query_id (string): a UUID
            typeahead_active (string): boolean value or None Example: 'None'.

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        url = f"{self.base_url}/api/search_reddit_names"
        query_params = {k: v for k, v in [('exact', exact), ('include_over_18', include_over_18), ('include_unadvertisable', include_unadvertisable), ('query', query), ('search_query_id', search_query_id), ('typeahead_active', typeahead_active)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_subreddit_autocomplete(self, include_over_18=None, include_profiles=None, query=None) -> Any:
        """
        Search for subreddits.

        Args:
            include_over_18 (string): boolean value (true, false)
            include_profiles (string): boolean value (true, false)
            query (string): a string up to 25 characters long, consisting of printable characters.

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        url = f"{self.base_url}/api/subreddit_autocomplete"
        query_params = {k: v for k, v in [('include_over_18', include_over_18), ('include_profiles', include_profiles), ('query', query)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_subreddit_autocomplete_v2(self, include_over_18=None, include_profiles=None, limit=None, query=None, search_query_id=None, typeahead_active=None) -> Any:
        """
        Search for subreddits.

        Args:
            include_over_18 (string): boolean value (true, false)
            include_profiles (string): boolean value (true, false)
            limit (string): an integer between 1 and 10 (default: 5)
            query (string): a string up to 25 characters long, consisting of printable characters.
            search_query_id (string): a UUID
            typeahead_active (string): boolean value (true, false) or None

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        url = f"{self.base_url}/api/subreddit_autocomplete_v2"
        query_params = {k: v for k, v in [('include_over_18', include_over_18), ('include_profiles', include_profiles), ('limit', limit), ('query', query), ('search_query_id', search_query_id), ('typeahead_active', typeahead_active)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_subreddit_post_requirements(self, subreddit) -> Any:
        """
        Get the post requirements for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/api/v1/{subreddit}/post_requirements"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_banned(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None, user=None) -> Any:
        """
        Get the banned users in a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits
            user (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/banned"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about(self, subreddit) -> Any:
        """
        Get the about information for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_edit(self, subreddit) -> Any:
        """
        Get the edit information for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/edit"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_contributors(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None, user=None) -> Any:
        """
        Get the contributors for a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits
            user (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/contributors"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_moderators(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None, user=None) -> Any:
        """
        Get the moderators for a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits
            user (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/moderators"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_muted(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None, user=None) -> Any:
        """
        Get the muted users for a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits
            user (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/muted"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_rules(self, subreddit) -> Any:
        """
        Get the rules for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/rules"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_sticky(self, subreddit, num=None) -> Any:
        """
        Get the sticky posts for a subreddit.

        Args:
            subreddit (string): subreddit
            num (string): an integer between 1 and 2 (default: 1)

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/sticky"
        query_params = {k: v for k, v in [('num', num)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_traffic(self, subreddit) -> Any:
        """
        Get the traffic for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/traffic"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_wikibanned(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None, user=None) -> Any:
        """
        Get the wikibanned users for a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits
            user (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/wikibanned"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_about_wikicontributors(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None, user=None) -> Any:
        """
        Get the wikicontributors for a subreddit.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits
            user (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/about/wikicontributors"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail), ('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_submit_text(self, subreddit) -> Any:
        """
        Get the submit text for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/submit_text"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def subreddits_mine_where(self, where, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the subreddits the current user has access to.

        Args:
            where (string): where
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if where is None:
            raise ValueError("Missing required parameter 'where'")
        url = f"{self.base_url}/subreddits/mine/{where}"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def subreddits_search(self, after=None, before=None, count=None, limit=None, q=None, search_query_id=None, show=None, show_users=None, sort=None, sr_detail=None, typeahead_active=None) -> Any:
        """
        Search for subreddits.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            q (string): a search query
            search_query_id (string): a UUID
            show (string): (optional) the string "all"
            show_users (string): boolean value (true, false)
            sort (string): one of (relevance, activity)
            sr_detail (string): (optional) expand subreddits
            typeahead_active (string): boolean value (true, false) or None

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        url = f"{self.base_url}/subreddits/search"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('q', q), ('search_query_id', search_query_id), ('show', show), ('show_users', show_users), ('sort', sort), ('sr_detail', sr_detail), ('typeahead_active', typeahead_active)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def subreddits_where(self, where, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the subreddits the current user has access to.

        Args:
            where (string): where
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            subreddits
        """
        if where is None:
            raise ValueError("Missing required parameter 'where'")
        url = f"{self.base_url}/subreddits/{where}"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_user_data_by_account_ids(self, ids=None) -> Any:
        """
        Get the user data by account IDs.

        Args:
            ids (string): A comma-separated list of account fullnames

        Returns:
            Any: API response data.

        Tags:
            users
        """
        url = f"{self.base_url}/api/user_data_by_account_ids"
        query_params = {k: v for k, v in [('ids', ids)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_username_available(self, user=None) -> Any:
        """
        Check if a username is available.

        Args:
            user (string): a valid, unused, username

        Returns:
            Any: API response data.

        Tags:
            users
        """
        url = f"{self.base_url}/api/username_available"
        query_params = {k: v for k, v in [('user', user)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_me_friends_username1(self, username, id=None) -> Any:
        """
        Get a user's friends.

        Args:
            username (string): username
            id (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            users
        """
        if username is None:
            raise ValueError("Missing required parameter 'username'")
        url = f"{self.base_url}/api/v1/me/friends/{username}"
        query_params = {k: v for k, v in [('id', id)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_me_friends_username(self, username, id=None) -> Any:
        """
        Delete a user's friend.

        Args:
            username (string): username
            id (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            users
        """
        if username is None:
            raise ValueError("Missing required parameter 'username'")
        url = f"{self.base_url}/api/v1/me/friends/{username}"
        query_params = {k: v for k, v in [('id', id)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def api_v1_user_username_trophies(self, username, id=None) -> Any:
        """
        Get a user's trophies.

        Args:
            username (string): username
            id (string): A valid, existing reddit username

        Returns:
            Any: API response data.

        Tags:
            users
        """
        if username is None:
            raise ValueError("Missing required parameter 'username'")
        url = f"{self.base_url}/api/v1/user/{username}/trophies"
        query_params = {k: v for k, v in [('id', id)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def user_username_about(self, username) -> Any:
        """
        Get the about information for a user.

        Args:
            username (string): username

        Returns:
            Any: API response data.

        Tags:
            users
        """
        if username is None:
            raise ValueError("Missing required parameter 'username'")
        url = f"{self.base_url}/user/{username}/about"
        query_params = {k: v for k, v in [('username', username)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def user_username_where(self, username, where, after=None, before=None, context=None, count=None, limit=None, show=None, sort=None, sr_detail=None, t=None, type=None) -> Any:
        """
        Get the user's posts or comments.

        Args:
            username (string): username
            where (string): where
            after (string): fullname of a thing
            before (string): fullname of a thing
            context (string): an integer between 2 and 10
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): one of (given)
            sort (string): one of (hot, new, top, controversial)
            sr_detail (string): (optional) expand subreddits
            t (string): one of (hour, day, week, month, year, all)
            type (string): one of (links, comments)

        Returns:
            Any: API response data.

        Tags:
            users
        """
        if username is None:
            raise ValueError("Missing required parameter 'username'")
        if where is None:
            raise ValueError("Missing required parameter 'where'")
        url = f"{self.base_url}/user/{username}/{where}"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('context', context), ('count', count), ('limit', limit), ('show', show), ('sort', sort), ('sr_detail', sr_detail), ('t', t), ('type', type), ('username', username)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def users_search(self, after=None, before=None, count=None, limit=None, q=None, search_query_id=None, show=None, sort=None, sr_detail=None, typeahead_active=None) -> Any:
        """
        Search for users.

        Args:
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            q (string): a search query
            search_query_id (string): a UUID
            show (string): (optional) the string "all"
            sort (string): one of (relevance, activity)
            sr_detail (string): (optional) expand subreddits
            typeahead_active (string): boolean value (true, false) or None

        Returns:
            Any: API response data.

        Tags:
            users
        """
        url = f"{self.base_url}/users/search"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('q', q), ('search_query_id', search_query_id), ('show', show), ('sort', sort), ('sr_detail', sr_detail), ('typeahead_active', typeahead_active)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def users_where(self, where, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the user's posts or comments.

        Args:
            where (string): where
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all"
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            users
        """
        if where is None:
            raise ValueError("Missing required parameter 'where'")
        url = f"{self.base_url}/users/{where}"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_widgets(self, subreddit) -> Any:
        """
        Get the widgets for a subreddit.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            widgets
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/api/widgets"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_widget_order_section(self, subreddit, section, items=None) -> Any:
        """
        Get the widget order for a subreddit.

        Args:
            subreddit (string): subreddit
            section (string): section

        Returns:
            Any: API response data.

        Tags:
            widgets
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if section is None:
            raise ValueError("Missing required parameter 'section'")
        # Use items array directly as request body
        request_body = items
        url = f"{self.base_url}/r/{subreddit}/api/widget_order/{section}"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_api_widget_widget_id(self, subreddit, widget_id) -> Any:
        """
        Delete a widget.

        Args:
            subreddit (string): subreddit
            widget_id (string): widget_id

        Returns:
            Any: API response data.

        Tags:
            widgets
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if widget_id is None:
            raise ValueError("Missing required parameter 'widget_id'")
        url = f"{self.base_url}/r/{subreddit}/api/widget/{widget_id}"
        query_params = {}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_wiki_discussions_page(self, subreddit, page, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the discussions for a wiki page.

        Args:
            subreddit (string): subreddit
            page (string): page
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            wiki
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if page is None:
            raise ValueError("Missing required parameter 'page'")
        url = f"{self.base_url}/r/{subreddit}/wiki/discussions/{page}"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('page', page), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_wiki_page(self, subreddit, page, v=None, v2=None) -> Any:
        """
        Get a wiki page.

        Args:
            subreddit (string): subreddit
            page (string): page
            v (string): a wiki revision ID
            v2 (string): a wiki revision ID

        Returns:
            Any: API response data.

        Tags:
            wiki
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if page is None:
            raise ValueError("Missing required parameter 'page'")
        url = f"{self.base_url}/r/{subreddit}/wiki/{page}"
        query_params = {k: v for k, v in [('v', v), ('v2', v2)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_wiki_pages(self, subreddit) -> Any:
        """
        Get the pages for a wiki.

        Args:
            subreddit (string): subreddit

        Returns:
            Any: API response data.

        Tags:
            wiki
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/wiki/pages"
        query_params = {}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_wiki_revisions(self, subreddit, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the revisions for a wiki.

        Args:
            subreddit (string): subreddit
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            wiki
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        url = f"{self.base_url}/r/{subreddit}/wiki/revisions"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_wiki_revisions_page(self, subreddit, page, after=None, before=None, count=None, limit=None, show=None, sr_detail=None) -> Any:
        """
        Get the revisions for a wiki page.

        Args:
            subreddit (string): subreddit
            page (string): page
            after (string): fullname of a thing
            before (string): fullname of a thing
            count (string): a positive integer (default: 0)
            limit (string): the maximum number of items desired (default: 25, maximum: 100)
            show (string): (optional) the string "all" Example: 'all'.
            sr_detail (string): (optional) expand subreddits

        Returns:
            Any: API response data.

        Tags:
            wiki
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if page is None:
            raise ValueError("Missing required parameter 'page'")
        url = f"{self.base_url}/r/{subreddit}/wiki/revisions/{page}"
        query_params = {k: v for k, v in [('after', after), ('before', before), ('count', count), ('limit', limit), ('page', page), ('show', show), ('sr_detail', sr_detail)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def r_subreddit_wiki_settings_page(self, subreddit, page) -> Any:
        """
        Get the settings for a wiki page.

        Args:
            subreddit (string): subreddit
            page (string): page

        Returns:
            Any: API response data.

        Tags:
            wiki
        """
        if subreddit is None:
            raise ValueError("Missing required parameter 'subreddit'")
        if page is None:
            raise ValueError("Missing required parameter 'page'")
        url = f"{self.base_url}/r/{subreddit}/wiki/settings/{page}"
        query_params = {k: v for k, v in [('page', page)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_tools(self):
        return [
            self.get_subreddit_posts,
            self.search_subreddits,
            self.get_post_flairs,
            self.create_post,
            self.get_comment_by_id,
            self.post_comment,
            self.edit_content,
            self.delete_content,
        # Auto Generated from openapi spec
            self.api_v1_me,
            self.api_v1_me_karma,
            self.api_v1_me_prefs,
            self.api_v1_me_prefs1,
            self.api_v1_me_trophies,
            self.prefs_friends,
            self.prefs_blocked,
            self.prefs_messaging,
            self.prefs_trusted,
            self.api_needs_captcha,
            self.api_v1_collections_collection,
            self.api_v1_collections_subreddit_collections,
            self.api_v1_subreddit_emoji_emoji_name,
            self.api_v1_subreddit_emojis_all,
            self.r_subreddit_api_flair,
            self.r_subreddit_api_flairlist,
            self.r_subreddit_api_link_flair,
            self.r_subreddit_api_link_flair_v2,
            self.r_subreddit_api_user_flair,
            self.r_subreddit_api_user_flair_v2,
            self.api_info,
            self.r_subreddit_api_info,
            self.api_morechildren,
            self.api_saved_categories,
            self.req,
            self.best,
            self.by_id_names,
            self.comments_article,
            self.controversial,
            self.duplicates_article,
            self.hot,
            self.new,
            self.r_subreddit_comments_article,
            self.r_subreddit_controversial,
            self.r_subreddit_hot,
            self.r_subreddit_new,
            self.r_subreddit_random,
            self.r_subreddit_rising,
            self.r_subreddit_top,
            self.random,
            self.rising,
            self.top,
            self.api_saved_media_text,
            self.api_v1_scopes,
            self.r_subreddit_api_saved_media_text,
            self.r_subreddit_about_log,
            self.r_subreddit_about_edited,
            self.r_subreddit_about_modqueue,
            self.r_subreddit_about_reports,
            self.r_subreddit_about_spam,
            self.r_subreddit_about_unmoderated,
            self.r_subreddit_stylesheet,
            self.stylesheet,
            self.api_mod_notes1,
            self.api_mod_notes,
            self.api_mod_notes_recent,
            self.api_multi_mine,
            self.api_multi_user_username,
            self.api_multi_multipath1,
            self.api_multi_multipath,
            self.api_multi_multipath_description,
            self.api_multi_multipath_rsubreddit1,
            self.api_multi_multipath_rsubreddit,
            self.api_mod_conversations,
            self.api_mod_conversations_conversation_id,
            self.api_mod_conversations_conversation_id_highlight,
            self.api_mod_conversations_conversation_id_unarchive,
            self.api_mod_conversations_conversation_id_unban,
            self.api_mod_conversations_conversation_id_unmute,
            self.api_mod_conversations_conversation_id_user,
            self.api_mod_conversations_subreddits,
            self.api_mod_conversations_unread_count,
            self.message_inbox,
            self.message_sent,
            self.message_unread,
            self.search,
            self.r_subreddit_search,
            self.api_search_reddit_names,
            self.api_subreddit_autocomplete,
            self.api_subreddit_autocomplete_v2,
            self.api_v1_subreddit_post_requirements,
            self.r_subreddit_about_banned,
            self.r_subreddit_about,
            self.r_subreddit_about_edit,
            self.r_subreddit_about_contributors,
            self.r_subreddit_about_moderators,
            self.r_subreddit_about_muted,
            self.r_subreddit_about_rules,
            self.r_subreddit_about_sticky,
            self.r_subreddit_about_traffic,
            self.r_subreddit_about_wikibanned,
            self.r_subreddit_about_wikicontributors,
            self.r_subreddit_api_submit_text,
            self.subreddits_mine_where,
            self.subreddits_search,
            self.subreddits_where,
            self.api_user_data_by_account_ids,
            self.api_username_available,
            self.api_v1_me_friends_username1,
            self.api_v1_me_friends_username,
            self.api_v1_user_username_trophies,
            self.user_username_about,
            self.user_username_where,
            self.users_search,
            self.users_where,
            self.r_subreddit_api_widgets,
            self.r_subreddit_api_widget_order_section,
            self.r_subreddit_api_widget_widget_id,
            self.r_subreddit_wiki_discussions_page,
            self.r_subreddit_wiki_page,
            self.r_subreddit_wiki_pages,
            self.r_subreddit_wiki_revisions,
            self.r_subreddit_wiki_revisions_page,
            self.r_subreddit_wiki_settings_page,
            self.get_post_comments_json,
        ]

