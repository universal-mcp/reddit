# RedditApp MCP Server

An MCP Server for the RedditApp API.

## 🛠️ Tool List

This is automatically generated from OpenAPI schema for the RedditApp API.


| Tool | Description |
|------|-------------|
| `get_subreddit_posts` | Retrieves and formats top posts from a specified subreddit within a given timeframe using the Reddit API |
| `search_subreddits` | Searches Reddit for subreddits matching a given query string and returns a formatted list of results including subreddit names, subscriber counts, and descriptions. |
| `get_post_flairs` | Retrieves a list of available post flairs for a specified subreddit using the Reddit API. |
| `create_post` | Creates a new Reddit post in a specified subreddit with support for text posts, link posts, and image posts |
| `get_comment_by_id` | Retrieves a specific Reddit comment using its unique identifier. |
| `post_comment` | Posts a comment to a Reddit post or comment using the Reddit API |
| `edit_content` | Edits the text content of an existing Reddit post or comment using the Reddit API |
| `delete_content` | Deletes a specified Reddit post or comment using the Reddit API. |
| `api_v1_me` | Get the current user's information. |
| `api_v1_me_karma` | Get the current user's karma. |
| `api_v1_me_prefs` | Get the current user's preferences. |
| `api_v1_me_prefs1` | Update the current user's preferences. |
| `api_v1_me_trophies` | Get the current user's trophies. |
| `prefs_friends` | Get the current user's friends. |
| `prefs_blocked` | Get the current user's blocked users. |
| `prefs_messaging` | Get the current user's messaging preferences. |
| `prefs_trusted` | Get the current user's trusted users. |
| `api_needs_captcha` | Check if the current user needs a captcha. |
| `api_v1_collections_collection` | Get a collection by ID. |
| `api_v1_collections_subreddit_collections` | Get the current user's subreddit collections. |
| `api_v1_subreddit_emoji_emoji_name` | Get an emoji by name. |
| `api_v1_subreddit_emojis_all` | Get all emojis for a subreddit. |
| `r_subreddit_api_flair` | Get the current user's flair for a subreddit. |
| `r_subreddit_api_flairlist` | Get the current user's flair list for a subreddit. |
| `r_subreddit_api_link_flair` | Get the current user's link flair for a subreddit. |
| `r_subreddit_api_link_flair_v2` | Get the current user's link flair for a subreddit. |
| `r_subreddit_api_user_flair` | Get the current user's user flair for a subreddit. |
| `r_subreddit_api_user_flair_v2` | Get the current user's user flair for a subreddit. |
| `api_info` | Get information about a link or comment. |
| `r_subreddit_api_info` | Get information about a link or comment in a subreddit. |
| `api_morechildren` | Get more children for a link or comment. |
| `api_saved_categories` | Get the current user's saved categories. |
| `req` | Get the current user's requests. |
| `best` | Get the best posts. |
| `by_id_names` | Get posts by ID. |
| `comments_article` | Get comments for a post. |
| `controversial` | Get the most controversial posts. |
| `duplicates_article` | Get duplicate posts. |
| `hot` | Get the hottest posts. |
| `new` | Get the newest posts. |
| `r_subreddit_comments_article` | Get comments for a post in a subreddit. |
| `r_subreddit_controversial` | Get the most controversial posts in a subreddit. |
| `r_subreddit_hot` | Get the hottest posts in a subreddit. |
| `r_subreddit_new` | Get the newest posts in a subreddit. |
| `r_subreddit_random` | Get a random post in a subreddit. |
| `r_subreddit_rising` | Get the rising posts in a subreddit. |
| `r_subreddit_top` | Get the top posts in a subreddit. |
| `random` | Get a random post. |
| `rising` | Get the rising posts. |
| `top` | Get the top posts. |
| `api_saved_media_text` | Get the text of a saved media. |
| `api_v1_scopes` | Get the current user's scopes. |
| `r_subreddit_api_saved_media_text` | Get the text of a saved media in a subreddit. |
| `r_subreddit_about_log` | Get the log of a subreddit. |
| `r_subreddit_about_edited` | Get the edited posts in a subreddit. |
| `r_subreddit_about_modqueue` | Get the modqueue in a subreddit. |
| `r_subreddit_about_reports` | Get the reports in a subreddit. |
| `r_subreddit_about_spam` | Get the spam posts in a subreddit. |
| `r_subreddit_about_unmoderated` | Get the unmoderated posts in a subreddit. |
| `r_subreddit_stylesheet` | Get the stylesheet of a subreddit. |
| `stylesheet` | Get the stylesheet of the current user. |
| `api_mod_notes1` | Get the mod notes of a subreddit. |
| `api_mod_notes` | Delete a mod note. |
| `api_mod_notes_recent` | Get the recent mod notes. |
| `api_multi_mine` | Get the current user's multi. |
| `api_multi_user_username` | Get a user's multi. |
| `api_multi_multipath1` | Get a multi. |
| `api_multi_multipath` | Delete a multi. |
| `api_multi_multipath_description` | Get a multi's description. |
| `api_multi_multipath_rsubreddit1` | Get a multi's subreddit. |
| `api_multi_multipath_rsubreddit` | Delete a multi's subreddit. |
| `api_mod_conversations` | Get the mod conversations. |
| `api_mod_conversations_conversation_id` | Get a mod conversation. |
| `api_mod_conversations_conversation_id_highlight` | Highlight a mod conversation. |
| `api_mod_conversations_conversation_id_unarchive` | Unarchive a mod conversation. |
| `api_mod_conversations_conversation_id_unban` | Unban a mod conversation. |
| `api_mod_conversations_conversation_id_unmute` | Unmute a mod conversation. |
| `api_mod_conversations_conversation_id_user` | Get a mod conversation's user. |
| `api_mod_conversations_subreddits` | Get the mod conversations' subreddits. |
| `api_mod_conversations_unread_count` | Get the unread count of the mod conversations. |
| `message_inbox` | Get the current user's inbox. |
| `message_sent` | Get the current user's sent messages. |
| `message_unread` | Get the current user's unread messages. |
| `search` | Search for posts, comments, and users. |
| `r_subreddit_search` | Search for posts, comments, and users in a subreddit. |
| `api_search_reddit_names` | Search for subreddits. |
| `api_subreddit_autocomplete` | Search for subreddits. |
| `api_subreddit_autocomplete_v2` | Search for subreddits. |
| `api_v1_subreddit_post_requirements` | Get the post requirements for a subreddit. |
| `r_subreddit_about_banned` | Get the banned users in a subreddit. |
| `r_subreddit_about` | Get the about information for a subreddit. |
| `r_subreddit_about_edit` | Get the edit information for a subreddit. |
| `r_subreddit_about_contributors` | Get the contributors for a subreddit. |
| `r_subreddit_about_moderators` | Get the moderators for a subreddit. |
| `r_subreddit_about_muted` | Get the muted users for a subreddit. |
| `r_subreddit_about_rules` | Get the rules for a subreddit. |
| `r_subreddit_about_sticky` | Get the sticky posts for a subreddit. |
| `r_subreddit_about_traffic` | Get the traffic for a subreddit. |
| `r_subreddit_about_wikibanned` | Get the wikibanned users for a subreddit. |
| `r_subreddit_about_wikicontributors` | Get the wikicontributors for a subreddit. |
| `r_subreddit_api_submit_text` | Get the submit text for a subreddit. |
| `subreddits_mine_where` | Get the subreddits the current user has access to. |
| `subreddits_search` | Search for subreddits. |
| `subreddits_where` | Get the subreddits the current user has access to. |
| `api_user_data_by_account_ids` | Get the user data by account IDs. |
| `api_username_available` | Check if a username is available. |
| `api_v1_me_friends_username1` | Get a user's friends. |
| `api_v1_me_friends_username` | Delete a user's friend. |
| `api_v1_user_username_trophies` | Get a user's trophies. |
| `user_username_about` | Get the about information for a user. |
| `user_username_where` | Get the user's posts or comments. |
| `users_search` | Search for users. |
| `users_where` | Get the user's posts or comments. |
| `r_subreddit_api_widgets` | Get the widgets for a subreddit. |
| `r_subreddit_api_widget_order_section` | Get the widget order for a subreddit. |
| `r_subreddit_api_widget_widget_id` | Delete a widget. |
| `r_subreddit_wiki_discussions_page` | Get the discussions for a wiki page. |
| `r_subreddit_wiki_page` | Get a wiki page. |
| `r_subreddit_wiki_pages` | Get the pages for a wiki. |
| `r_subreddit_wiki_revisions` | Get the revisions for a wiki. |
| `r_subreddit_wiki_revisions_page` | Get the revisions for a wiki page. |
| `r_subreddit_wiki_settings_page` | Get the settings for a wiki page. |
