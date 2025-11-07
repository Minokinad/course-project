from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services import employee_service
from src.auth.dependencies import require_admin

router = APIRouter(prefix="/employees", tags=["Employees"], dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def list_employees_page(
    request: Request,
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query('asc')
):
    employees = await employee_service.fetch_all_employees(sort_by=sort_by, order=order)
    return templates.TemplateResponse("employees.html", {
        "request": request,
        "employees": employees,
        "active_page": "employees",
        "sort_by": sort_by,
        "order": order
    })

@router.get("/new", response_class=HTMLResponse)
async def new_employee_form(request: Request):
    return templates.TemplateResponse("employee_form.html", {
        "request": request,
        "employee": None,
        "active_page": "employees"
    })

@router.post("/new")
async def create_employee_action(
    request: Request,
    name: str = Form(...),
    email: str = Form(...), # Добавлено поле email
    login: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    await employee_service.create_employee(name, email, login, password, role, user_login=request.state.user_login)
    return RedirectResponse(url="/employees", status_code=303)

@router.get("/{emp_id}/edit", response_class=HTMLResponse)
async def edit_employee_form(request: Request, emp_id: int):
    employee = await employee_service.fetch_employee_by_id(emp_id)
    return templates.TemplateResponse("employee_form.html", {
        "request": request,
        "employee": employee,
        "active_page": "employees"
    })

@router.post("/{emp_id}/edit")
async def update_employee_action(
    request: Request,
    emp_id: int,
    name: str = Form(...),
    email: str = Form(...), # Добавлено поле email
    login: str = Form(...),
    role: str = Form(...),
    password: str = Form(None)
):
    await employee_service.update_employee(emp_id, name, email, login, role, password, user_login=request.state.user_login)
    return RedirectResponse(url="/employees", status_code=303)


@router.delete("/{emp_id}", response_class=HTMLResponse)
async def delete_employee_htmx(request: Request, emp_id: int):
    if request.state.user and request.state.user['employee_id'] == emp_id:
        return HTMLResponse(content="<div class='alert alert-danger'>Нельзя удалить собственную учетную запись.</div>", status_code=400)

    await employee_service.delete_employee(emp_id, user_login=request.state.user_login)
    return HTMLResponse(content="", status_code=200)