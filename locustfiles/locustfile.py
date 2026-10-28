"""
Locustfile for load testing store_manager.py
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
import random
from locust import HttpUser, task, between

class FlaskAPIUser(HttpUser):
    # Wait time between requests (1-3 seconds)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called every time a Locust user spawns"""
        print("Welcome, user!")

    # @task(1)
    # def test_rate_limit(self):
    #   """Test pour vérifier le rate limiting"""
    #   payload = {
    #       "user_id": random.randint(1, 3),
    #       "items": [{"product_id": random.randint(1, 4), "quantity": random.randint(1, 10)}] 
    #   }   
      
    #   response = self.client.post(
    #       "/store-manager-api/orders",
    #       json=payload
    #   )
      
    #   if response.status_code == 503:  # HTTP 503 Service Unavailable
    #       print("Rate limit atteint!")


    @task
    def order_and_payment_workflow(self):
        """Simulate a complete order and payment workflow"""
        user_id = random.randint(1, 3)
        order_payload = {
            "user_id": user_id,
            "items": [{"product_id": random.randint(1, 4), "quantity": random.randint(1, 10)}] 
      }   

        with self.client.post(
            "/store-manager-api/orders",
            json=order_payload,
            name="POST create order",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201):
                response.failure(
                    f"Order creation failed: HTTP {response.status_code}"
                )
                return

            try:
                order_data = response.json()
                order_id = order_data["order_id"]
            except (ValueError, KeyError):
                response.failure("Order response has no order_id")
                return

            response.success()


        payment_payload = {
            "user_id": user_id,
            "order_id": order_id,
            "total_amount": random.uniform(10.0, 100.0)  # Random total amount for the payment
        }

        with self.client.post(
            "/payments-api/payments",
            json=payment_payload,
            name="POST create payment",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201):
                response.failure(
                    f"Payment creation failed: HTTP {response.status_code}"
                )
                return

            try:
                payment_id = response.json()["payment_id"]
            except (ValueError, KeyError):
                response.failure("Payment response has no payment_id")
                return

            response.success()

        credit_card_data = {
            "cardNumber": 9999999999999,
            "cardCode": 123,
            "expirationDate": "2030-01-05",
        }

        with self.client.post(
            f"/payments-api/payments/process/{payment_id}",
            json=credit_card_data,
            name="POST process payment",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Payment processing failed: HTTP {response.status_code}"
                )
                return

            try:
                result = response.json()
                if (
                    result.get("order_id") != order_id
                    or result.get("payment_id") != payment_id
                    or result.get("is_paid") is not True
                ):
                    response.failure(
                        f"Unexpected payment result: {result}"
                    )
                    return
            except ValueError:
                response.failure("Payment response is not valid JSON")
                return

            response.success()
