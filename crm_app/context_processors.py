from .models import FAQ, Notification


def faq_count(request):
    if request.user.is_authenticated:
        count = FAQ.objects.all().count()
    else:
        count = 0
    return {"faq_count": count}


def current_login(request):
    if request.user and request.user.is_authenticated:
        if request.user.user_type == "4":
            user = request.user
            agent_id = user.agent.id
            notification = Notification.objects.filter(
                agent=agent_id, is_seen=False
            ).order_by("-id")
            notification_Count = Notification.objects.filter(
                agent=agent_id, is_seen=False
            ).count()

            return {
                "agent_id": agent_id,
                "notification": notification,
                "notification_Count": notification_Count,
            }
        elif request.user.user_type == "5":
            user = request.user
            agent_id = user.outsourcingagent.id
            notification = Notification.objects.filter(
                outsourceagent=agent_id, is_seen=False
            ).order_by("-id")
            notification_Count = Notification.objects.filter(
                outsourceagent=agent_id, is_seen=False
            ).count()

            return {
                "agent_id": agent_id,
                "notification": notification,
                "notification_Count": notification_Count,
            }
        elif request.user.user_type == "3":
            user = request.user
            emp_idd = user.employee.id
            notification = Notification.objects.filter(
                employee=emp_idd, is_seen=False
            ).order_by("-id")
            notification_Count = Notification.objects.filter(
                employee=user.employee, is_seen=False
            ).count()

            return {
                "emp_idd": emp_idd,
                "notification": notification,
                "notification_Count": notification_Count,
            }

        elif request.user.user_type == "2":
            user = request.user

            notification = Notification.objects.filter(is_seen=False).order_by("-id")
            notification_Count = Notification.objects.filter(is_seen=False).count()

            return {
                "notification": notification,
                "notification_Count": notification_Count,
            }

    return {}
