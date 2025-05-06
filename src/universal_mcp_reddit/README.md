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
| `api_v1_me` | /api/v1/me |
| `api_v1_me_karma` | /api/v1/me/karma |
| `api_v1_me_prefs` | /api/v1/me/prefs |
| `api_v1_me_prefs1` | /api/v1/me/prefs |
| `api_v1_me_trophies` | /api/v1/me/trophies |
| `prefs_friends` | /prefs/friends |
| `prefs_blocked` | /prefs/blocked |
| `prefs_messaging` | /prefs/messaging |
| `prefs_trusted` | /prefs/trusted |
| `api_needs_captcha` | /api/needs_captcha |
| `api_v1_collections_collection` | /api/v1/collections/collection |
| `api_v1_collections_subreddit_collections` | /api/v1/collections/subreddit_collections |
| `api_v1_subreddit_emoji_emoji_name` | /api/v1/:subreddit/emoji/:emoji_name |
| `api_v1_subreddit_emojis_all` | /api/v1/:subreddit/emojis/all |
| `r_subreddit_api_flair` | /r/:subreddit/api/flair |
| `r_subreddit_api_flairlist` | /r/:subreddit/api/flairlist |
| `r_subreddit_api_link_flair` | /r/:subreddit/api/link_flair |
| `r_subreddit_api_link_flair_v2` | /r/:subreddit/api/link_flair_v2 |
| `r_subreddit_api_user_flair` | /r/:subreddit/api/user_flair |
| `r_subreddit_api_user_flair_v2` | /r/:subreddit/api/user_flair_v2 |
| `api_info` | /api/info |
| `r_subreddit_api_info` | r/:subreddit/api/info |
| `api_morechildren` | /api/morechildren |
| `api_saved_categories` | /api/saved_categories |
| `req` | /req |
| `best` | /best |
| `by_id_names` | /by_id/:names |
| `comments_article` | /comments/:article |
| `controversial` | /controversial |
| `duplicates_article` | /duplicates/:article |
| `hot` | /hot |
| `new` | /new |
| `r_subreddit_comments_article` | /r/:subreddit/comments/:article |
| `r_subreddit_controversial` | /r/:subreddit/controversial |
| `r_subreddit_hot` | /r/:subreddit/hot |
| `r_subreddit_new` | /r/:subreddit/new |
| `r_subreddit_random` | /r/:subreddit/random |
| `r_subreddit_rising` | /r/:subreddit/rising |
| `r_subreddit_top` | /r/:subreddit/top |
| `random` | /random |
| `rising` | /rising |
| `top` | /top |
| `api_saved_media_text` | /api/saved_media_text |
| `api_v1_scopes` | /api/v1/scopes |
| `r_subreddit_api_saved_media_text` | /r/:subreddit/api/saved_media_text |
| `r_subreddit_about_log` | /r/:subreddit/about/log |
| `r_subreddit_about_edited` | /r/:subreddit/about/edited |
| `r_subreddit_about_modqueue` | /r/:subreddit/about/modqueue |
| `r_subreddit_about_reports` | /r/:subreddit/about/reports |
| `r_subreddit_about_spam` | /r/:subreddit/about/spam |
| `r_subreddit_about_unmoderated` | /r/:subreddit/about/unmoderated |
| `r_subreddit_stylesheet` | /r/:subreddit/stylesheet |
| `stylesheet` | /stylesheet |
| `api_mod_notes1` | /api/mod/notes |
| `api_mod_notes` | /api/mod/notes |
| `api_mod_notes_recent` | /api/mod/notes/recent |
| `api_multi_mine` | /api/multi/mine |
| `api_multi_user_username` | /api/multi/user/:username |
| `api_multi_multipath1` | /api/multi/:multipath |
| `api_multi_multipath` | /api/multi/:multipath |
| `api_multi_multipath_description` | /api/multi/:multipath/description |
| `api_multi_multipath_rsubreddit1` | /api/multi/:multipath/r/:subreddit |
| `api_multi_multipath_rsubreddit` | /api/multi/:multipath/r/:subreddit |
| `api_mod_conversations` | /api/mod/conversations |
| `api_mod_conversations_conversation_id` | /api/mod/conversations/:conversation_id |
| `api_mod_conversations_conversation_id_highlight` | /api/mod/conversations/:conversation_id/highlight |
| `api_mod_conversations_conversation_id_unarchive` | /api/mod/conversations/:conversation_id/unarchive |
| `api_mod_conversations_conversation_id_unban` | /api/mod/conversations/:conversation_id/unban |
| `api_mod_conversations_conversation_id_unmute` | /api/mod/conversations/:conversation_id/unmute |
| `api_mod_conversations_conversation_id_user` | /api/mod/conversations/:conversation_id/user |
| `api_mod_conversations_subreddits` | /api/mod/conversations/subreddits |
| `api_mod_conversations_unread_count` | /api/mod/conversations/unread/count |
| `message_inbox` | /message/inbox |
| `message_sent` | /message/sent |
| `message_unread` | /message/unread |
| `search` | /search |
| `r_subreddit_search` | /r/:subreddit/search |
| `api_search_reddit_names` | /api/search_reddit_names |
| `api_subreddit_autocomplete` | /api/subreddit_autocomplete |
| `api_subreddit_autocomplete_v2` | /api/subreddit_autocomplete_v2 |
| `api_v1_subreddit_post_requirements` | /api/v1/:subreddit/post_requirements |
| `r_subreddit_about_banned` | /r/:subreddit/about/banned |
| `r_subreddit_about` | /r/:subreddit/about |
| `r_subreddit_about_edit` | /r/:subreddit/about/edit |
| `r_subreddit_about_contributors` | /r/:subreddit/about/contributors |
| `r_subreddit_about_moderators` | /r/:subreddit/about/moderators |
| `r_subreddit_about_muted` | /r/:subreddit/about/muted |
| `r_subreddit_about_rules` | /r/:subreddit/about/rules |
| `r_subreddit_about_sticky` | /r/:subreddit/about/sticky |
| `r_subreddit_about_traffic` | /r/:subreddit/about/traffic |
| `r_subreddit_about_wikibanned` | /r/:subreddit/about/wikibanned |
| `r_subreddit_about_wikicontributors` | /r/:subreddit/about/wikicontributors |
| `r_subreddit_api_submit_text` | /r/:subreddit/api/submit_text |
| `subreddits_mine_where` | /subreddits/mine/:where |
| `subreddits_search` | /subreddits/search |
| `subreddits_where` | /subreddits/:where |
| `api_user_data_by_account_ids` | /api/user_data_by_account_ids |
| `api_username_available` | /api/username_available |
| `api_v1_me_friends_username1` | /api/v1/me/friends/:username |
| `api_v1_me_friends_username` | /api/v1/me/friends/:username |
| `api_v1_user_username_trophies` | /api/v1/user/:username/trophies |
| `user_username_about` | /user/:username/about |
| `user_username_where` | /user/:username/:where |
| `users_search` | /users/search |
| `users_where` | /users/:where |
| `r_subreddit_api_widgets` | /r/:subreddit/api/widgets |
| `r_subreddit_api_widget_order_section` | /r/:subreddit/api/widget_order/:section |
| `r_subreddit_api_widget_widget_id` | /r/:subreddit/api/widget/:widget_id |
| `r_subreddit_wiki_discussions_page` | /r/:subreddit/wiki/discussions/:page |
| `r_subreddit_wiki_page` | /r/:subreddit/wiki/:page |
| `r_subreddit_wiki_pages` | /r/:subreddit/wiki/pages |
| `r_subreddit_wiki_revisions` | /r/:subreddit/wiki/revisions |
| `r_subreddit_wiki_revisions_page` | /r/:subreddit/wiki/revisions/:page |
| `r_subreddit_wiki_settings_page` | /r/:subreddit/wiki/settings/:page |
