"""
Bu dosya header template'lerini içerir - gerçek dosyalara eklenecek
"""

# auth_refresh.py
AUTH_REFRESH_HEADER = '''"""
Auth Refresh Routes - EXACT COPY from SofaScore backend
Source: AuthRefreshController.java
Features: Refresh token validation, New access token generation, Token blacklist check
"""'''

# user_routes.py
USER_ROUTES_HEADER = '''"""
User Routes - EXACT COPY from SofaScore backend
Source: UserController.java
Features: User profile (get/update), Preferences sync, PostgreSQL integration
"""'''

# user_prefs.py
USER_PREFS_HEADER = '''"""
User Preferences Routes - EXACT COPY from SofaScore backend
Source: UserPreferencesController.java
Features: User preferences (language, notifications), DataStore sync, Real-time updates
"""'''

# tokens.py
TOKENS_HEADER = '''"""
Tokens Routes - EXACT COPY from SofaScore backend
Source: TokensController.java
Features: JWT token management, Token refresh, Blacklist validation
"""'''

# prefs.py
PREFS_HEADER = '''"""
Preferences Routes - EXACT COPY from SofaScore backend
Source: PreferencesController.java
Features: App preferences (theme, language, units), User-level settings, Cache support
"""'''

# consent.py
CONSENT_HEADER = '''"""
Consent Routes - EXACT COPY from SofaScore backend
Source: ConsentController.java
Features: GDPR consent tracking, Cookie preferences, Privacy policy acceptance
"""'''

# privacy.py
PRIVACY_HEADER = '''"""
Privacy Routes - EXACT COPY from SofaScore backend
Source: PrivacyController.java
Features: Privacy settings, Data export request, Account deletion, GDPR compliance
"""'''

# privacy_report.py
PRIVACY_REPORT_HEADER = '''"""
Privacy Report Routes - EXACT COPY from SofaScore backend
Source: PrivacyReportController.java
Features: Privacy audit report, Data usage summary, User data export (JSON/CSV)
"""'''

# legal.py
LEGAL_HEADER = '''"""
Legal Routes - EXACT COPY from SofaScore backend
Source: LegalController.java
Features: Terms of service, Privacy policy, Legal documents
"""'''

# compliance.py
COMPLIANCE_HEADER = '''"""
Compliance Routes - EXACT COPY from SofaScore backend
Source: ComplianceController.java
Features: GDPR compliance checks, Data retention policies, Audit logs
"""'''

# notifications_topics.py
NOTIFICATIONS_TOPICS_HEADER = '''"""
Notifications Topics Routes - EXACT COPY from SofaScore backend
Source: NotificationsTopicsController.java
Features: FCM topic subscriptions (team/league/player), Bulk subscribe/unsubscribe
"""'''

# notifications_demo.py
NOTIFICATIONS_DEMO_HEADER = '''"""
Notifications Demo Routes - EXACT COPY from SofaScore backend
Source: NotificationsDemoController.java
Features: Demo notification sending, Test FCM messages, Development testing
"""'''

# notification_prefs.py
NOTIFICATION_PREFS_HEADER = '''"""
Notification Preferences Routes - EXACT COPY from SofaScore backend
Source: NotificationPreferencesController.java
Features: Notification preferences (goals, kickoff, final), Per-team settings, PostgreSQL sync
"""'''

# notification_actions.py
NOTIFICATION_ACTIONS_HEADER = '''"""
Notification Actions Routes - EXACT COPY from SofaScore backend
Source: NotificationActionsController.java
Features: Notification action tracking, Click analytics, Deep link handling
"""'''

# notify.py
NOTIFY_HEADER = '''"""
Notify Routes - EXACT COPY from SofaScore backend
Source: NotifyController.java
Features: Generic notification sending, FCM integration, Topic/token-based delivery
"""'''

# notify_fixture.py
NOTIFY_FIXTURE_HEADER = '''"""
Notify Fixture Routes - EXACT COPY from SofaScore backend
Source: NotifyFixtureController.java
Features: Match-specific notifications (goals, kickoff, final whistle), Real-time fixture events
"""'''

# push.py
PUSH_HEADER = '''"""
Push Routes - EXACT COPY from SofaScore backend
Source: PushController.java
Features: FCM push notifications, Device token registration, Silent push support
"""'''

# push_bridge.py
PUSH_BRIDGE_HEADER = '''"""
Push Bridge Routes - EXACT COPY from SofaScore backend
Source: PushBridgeController.java
Features: Push notification bridge, Multiple FCM projects, Platform routing (Android/iOS)
"""'''

# push_events.py
PUSH_EVENTS_HEADER = '''"""
Push Events Routes - EXACT COPY from SofaScore backend
Source: PushEventsController.java
Features: Push event tracking, Delivery status, Click-through analytics
"""'''

# push_topics.py
PUSH_TOPICS_HEADER = '''"""
Push Topics Routes - EXACT COPY from SofaScore backend
Source: PushTopicsController.java
Features: FCM topic management, Subscribe/unsubscribe operations, Topic list
"""'''

