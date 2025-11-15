from fastapi import FastAPI
from routers import booking, checkout, service_bot, validator

app = FastAPI(title="Snack Overflow API")

app.include_router(booking.router) #/booking
app.include_router(checkout.router) #/checkout
app.include_router(service_bot.router) #/service
app.include_router(validator.router) #/validate

@app.get("/")
def root():
    return {"message": "Backend OK"}
