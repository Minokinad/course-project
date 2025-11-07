from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from src.services import ticket_service, employee_service
from src.auth.dependencies import require_tech
from src.templating import templates

router = APIRouter(prefix="/tickets", tags=["Tickets"], dependencies=[Depends(require_tech)])


@router.get("", response_class=HTMLResponse)
async def list_tickets_page(
    request: Request,
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query('created_at'),
    order: Optional[str] = Query('desc')
):
    """
    Отображает страницу со списком всех заявок.
    """
    tickets = await ticket_service.fetch_all_tickets(status_filter=status, sort_by=sort_by, order=order)
    return templates.TemplateResponse("tickets_employee.html", {
        "request": request,
        "tickets": tickets,
        "active_page": "tickets",
        "current_status": status,
        "sort_by": sort_by,
        "order": order
    })


@router.get("/{ticket_id}", response_class=HTMLResponse)
async def ticket_details_page(request: Request, ticket_id: int):
    """
    Отображает страницу с деталями одной заявки и формой для её обновления.
    """
    ticket = await ticket_service.fetch_ticket_by_id(ticket_id)
    if not ticket:
        return RedirectResponse(url="/tickets", status_code=404)

    # Получаем сотрудников, которым можно назначить заявку (все, кроме админов, например)
    assignees = await employee_service.fetch_all_employees()

    return templates.TemplateResponse("ticket_detail_employee.html", {
        "request": request,
        "ticket": ticket,
        "assignees": assignees,
        "active_page": "tickets"
    })


@router.post("/{ticket_id}")
async def update_ticket_action(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
    assigned_to_id: Optional[int] = Form(None)
):
    """
    Обрабатывает обновление статуса и исполнителя заявки.
    """
    await ticket_service.update_ticket(
        ticket_id, status, assigned_to_id, user_login=request.state.user_login
    )
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)