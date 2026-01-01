import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from gym.models import Member
from django.utils import timezone

User = get_user_model()

def reproduce():
    email = "test_member_delete@example.com"
    
    # 1. Start clean
    User.objects.filter(email=email).delete()
    print(f"Cleaned up any existing user with {email}")

    # 2. Create User and Member
    user = User.objects.create_user(
        email=email,
        username=email,
        password="password123",
        first_name="Test",
        last_name="Member",
        role='member'
    )
    
    member = Member.objects.create(
        user=user,
        date_of_birth="1990-01-01",
        gender="Other",
        address="123 Test St",
        join_date=timezone.now().date(),
        status='active'
    )
    
    print(f"Created user {user.id} and member {member.id}")

    # 3. Simulate MemberDetailView.delete logic
    user_to_delete = member.user
    print(f"Retrieved user {user_to_delete.id} from member.user")
    
    print("Deleting user (cascading to member)...")
    user_to_delete.delete()
    
    # 4. Verify
    user_exists = User.objects.filter(email=email).exists()
    member_exists = Member.objects.filter(user__email=email).exists()
    
    print(f"User exists: {user_exists}")
    print(f"Member exists: {member_exists}")

    if user_exists or member_exists:
        print("FAIL: User or Member still exists after deletion!")
    else:
        print("SUCCESS: User and Member deleted.")

if __name__ == "__main__":
    reproduce()
