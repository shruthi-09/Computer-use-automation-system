from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio

app = FastAPI()

templates = Jinja2Templates(directory="demo_app/templates")

MEMBERS = {
    "12345": {
        "name": "Demo Member",
        "checking_balance": "$1,284.20",
        "savings_balance": "$4,821.77",
    },
    "77777": {
        "name": "Slow Demo Member",
        "checking_balance": "$500.00",
        "savings_balance": "$2,150.00",
    },
}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={}
    )


@app.post("/member", response_class=HTMLResponse)
async def member_search(
    request: Request,
    member_id: str = Form(...)
):
    if member_id == "99999":
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "title": "Member Not Found",
                "message": "No member exists with that ID."
            }
        )

    if member_id == "55555":
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "title": "Permission Denied",
                "message": "You do not have permission to view this member."
            }
        )

    if member_id == "88888":
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "title": "Application Error",
                "message": "The servicing system encountered an unexpected error."
            }
        )

    if member_id == "77777":
        await asyncio.sleep(3)

    member = MEMBERS.get(member_id)

    if not member:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "title": "Member Not Found",
                "message": "No member exists with that ID."
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="member.html",
        context={
            "member_id": member_id,
            "member": member
        }
    )