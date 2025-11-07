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
    Отображает страницу с деталями одной заявки, формой для её обновления и перепиской.
    """
    ticket = await ticket_service.fetch_ticket_by_id(ticket_id)
    if not ticket:
        return RedirectResponse(url="/tickets", status_code=404)

    assignees = await employee_service.fetch_all_employees()
    messages = await ticket_service.fetch_messages_for_ticket(ticket_id)

    return templates.TemplateResponse("ticket_detail_employee.html", {
        "request": request,
        "ticket": ticket,
        "assignees": assignees,
        "messages": messages,
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
    # ПРИМЕЧАНИЕ: Раньше было перенаправление на ту же страницу,
    # но лучше перенаправлять на общий список, чтобы было видно результат.
    # Вы можете вернуть f"/tickets/{ticket_id}", если предпочитаете.
    return RedirectResponse(url="/tickets", status_code=303)


# ОБРАТИТЕ ВНИМАНИЕ НА ЭТОТ ЭНДПОИНТ. СКОРЕЕ ВСЕГО, ОШИБКА БЫЛА ЗДЕСЬ.
@router.post("/{ticket_id}/add-message")
async def add_message_employee_action(
    request: Request,
    ticket_id: int,
    message_text: str = Form(...)
):
    """
    Обрабатывает добавление нового сообщения в заявку от сотрудника.
    """
    user = request.state.user
    # Проверяем, что пользователь существует и сообщение не пустое
    if user and message_text.strip():
        await ticket_service.add_message_to_ticket(
            ticket_id=ticket_id,
            message_text=message_text,
            employee_id=user['employee_id'],
            user_login=user['login']
        )
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)