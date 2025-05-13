from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
   
    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    facebook_link = models.CharField(max_length=255, blank=True)
    instagram_link = models.CharField(max_length=255, blank=True)
    twitter_link = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
             return self.username.username + ' added profile information'
    
class UserAvatar(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='avatars')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.profile.username.username} - {self.uploaded_at}"

    class Meta:
        ordering = ['-uploaded_at']

class Event(models.Model):
    CATEGORY_CHOICES = [
        ('Concerts', 'Concert'),
        ('Technology', 'Technology'),
        ('Food', 'Food & Drink'),
        ('Sports', 'Sports & Fitness'),
        ('Education', 'Education & Career'),
        ('Arts', 'Arts & Creativity'),
        ('Entertainment', 'Entertainment & Culture'),
    ]
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Concerts')
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, default='Pakistan')
    map_link = models.TextField(null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    is_free = models.BooleanField(default=False)
    carousel_image_1 = models.ImageField(upload_to='carousel_images/', null=True, blank=True)
    carousel_image_2 = models.ImageField(upload_to='carousel_images/', null=True, blank=True)
    carousel_image_3 = models.ImageField(upload_to='carousel_images/', null=True, blank=True)
    carousel_image_4 = models.ImageField(upload_to='carousel_images/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return self.name
    
class EventFace(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='faces')
    image = models.ImageField(upload_to='event_faces/')

    def __str__(self):
        return f"Face for {self.event.name}"
    
class EventHighlight(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='highlights')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"Highlight for {self.event.name}"


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} - {self.event.name}"

class BankAccount(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=255)
    account_title = models.CharField(max_length=255)
    iban_number = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.bank_name} - {self.account_title}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    ticket = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return self.ticket.price * self.quantity

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True) 
    is_redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} for {self.event.name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    item_price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.ticket_type.name} for Order #{self.order.id}"
    
class TicketSale(models.Model):
    event = models.ForeignKey(Event, related_name="ticket_sales", on_delete=models.CASCADE)
    ticket = models.ForeignKey(TicketType, related_name="sales", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Sale of {self.quantity} {self.ticket.name} for {self.event.name}"