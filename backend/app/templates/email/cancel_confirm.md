# Subscription Cancellation Confirmed

Hi {{customer_name}},

We've received your request to cancel your **{{plan_name}}** subscription.

## Cancellation Details

- **Effective Date**: {{effective_date}}
- **Reason**: {{reason}}
{% if reason_codes %}
- **Specific Issues**: {{reason_codes|join(', ')}}
{% endif %}
{% if notes %}
- **Your Feedback**: {{notes}}
{% endif %}

{% if is_immediate %}
Your subscription has been canceled immediately and your access has ended.
{% else %}
Your subscription will remain active until **{{effective_date}}**. You can continue using all features until then.

If you change your mind, you can reactivate your subscription at any time before {{effective_date}} by visiting your [subscription settings]({{settings_url}}).
{% endif %}

## What Happens Next

{% if not is_immediate %}
- You'll continue to have full access until {{effective_date}}
- We'll send you a reminder email 24 hours before your access ends
- Your data will be safely stored for 30 days after cancellation
{% else %}
- Your data will be safely stored for 30 days in case you want to return
{% endif %}
- No further charges will be made to your payment method

{% if not is_immediate %}
## Need Help?

If you're canceling due to technical issues or need assistance, our support team is here to help. Simply reply to this email or contact us at support@leadledgerpro.com.
{% endif %}

Thank you for using **{{brand_name}}**. We're sorry to see you go and would love to have you back in the future.

Best regards,  
The {{brand_name}} Team

---
*This email was sent because you canceled your subscription. If you have questions, contact us at support@leadledgerpro.com*