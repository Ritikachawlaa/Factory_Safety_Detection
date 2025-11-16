import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface Employee {
  id: string;
  employeeId: string;
  name: string;
  email: string;
  phone: string;
  department: string;
  designation: string;
  joiningDate: string;
  photoUrl: string;
  status: 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
}

export interface EmployeeCreateRequest {
  employeeId: string;
  name: string;
  email: string;
  phone: string;
  department: string;
  designation: string;
  joiningDate: string;
  photo: File;
}

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {
  private readonly API_URL = 'http://localhost:8000/api';
  
  // Signal-based state management
  employees = signal<Employee[]>([]);
  selectedEmployee = signal<Employee | null>(null);
  isLoading = signal(false);
  error = signal<string | null>(null);

  constructor(private http: HttpClient) {
    this.loadEmployees();
  }

  /**
   * Load all employees from the backend
   */
  loadEmployees(): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.http.get<Employee[]>(`${this.API_URL}/employees/`)
      .pipe(
        tap({
          next: (employees) => {
            this.employees.set(employees);
            this.isLoading.set(false);
          },
          error: (err) => {
            this.error.set('Failed to load employees');
            this.isLoading.set(false);
            console.error('Error loading employees:', err);
          }
        })
      )
      .subscribe();
  }

  /**
   * Get employee by ID
   */
  getEmployeeById(id: string): Observable<Employee> {
    return this.http.get<Employee>(`${this.API_URL}/employees/${id}/`);
  }

  /**
   * Create new employee with photo upload
   */
  createEmployee(data: EmployeeCreateRequest): Observable<Employee> {
    const formData = new FormData();
    formData.append('employeeId', data.employeeId);
    formData.append('name', data.name);
    formData.append('email', data.email);
    formData.append('phone', data.phone);
    formData.append('department', data.department);
    formData.append('designation', data.designation);
    formData.append('joiningDate', data.joiningDate);
    formData.append('photo', data.photo);
    formData.append('status', 'active');

    return this.http.post<Employee>(`${this.API_URL}/employees/`, formData)
      .pipe(
        tap({
          next: (employee) => {
            // Add to local state
            this.employees.update(employees => [...employees, employee]);
            console.log('✅ Employee created:', employee);
          },
          error: (err) => {
            this.error.set('Failed to create employee');
            console.error('❌ Error creating employee:', err);
          }
        })
      );
  }

  /**
   * Update employee details
   */
  updateEmployee(id: string, data: Partial<EmployeeCreateRequest>): Observable<Employee> {
    const formData = new FormData();
    
    if (data.employeeId) formData.append('employeeId', data.employeeId);
    if (data.name) formData.append('name', data.name);
    if (data.email) formData.append('email', data.email);
    if (data.phone) formData.append('phone', data.phone);
    if (data.department) formData.append('department', data.department);
    if (data.designation) formData.append('designation', data.designation);
    if (data.joiningDate) formData.append('joiningDate', data.joiningDate);
    if (data.photo) formData.append('photo', data.photo);

    return this.http.put<Employee>(`${this.API_URL}/employees/${id}/`, formData)
      .pipe(
        tap({
          next: (employee) => {
            // Update local state
            this.employees.update(employees => 
              employees.map(e => e.id === id ? employee : e)
            );
            console.log('✅ Employee updated:', employee);
          },
          error: (err) => {
            this.error.set('Failed to update employee');
            console.error('❌ Error updating employee:', err);
          }
        })
      );
  }

  /**
   * Delete employee
   */
  deleteEmployee(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/employees/${id}/`)
      .pipe(
        tap({
          next: () => {
            // Remove from local state
            this.employees.update(employees => 
              employees.filter(e => e.id !== id)
            );
            console.log('✅ Employee deleted:', id);
          },
          error: (err) => {
            this.error.set('Failed to delete employee');
            console.error('❌ Error deleting employee:', err);
          }
        })
      );
  }

  /**
   * Search employees by name or ID
   */
  searchEmployees(query: string): Employee[] {
    const lowerQuery = query.toLowerCase();
    return this.employees().filter(emp => 
      emp.name.toLowerCase().includes(lowerQuery) ||
      emp.employeeId.toLowerCase().includes(lowerQuery) ||
      emp.email.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Filter employees by department
   */
  filterByDepartment(department: string): Employee[] {
    return this.employees().filter(emp => emp.department === department);
  }

  /**
   * Get all departments
   */
  getAllDepartments(): string[] {
    const departments = new Set(this.employees().map(e => e.department));
    return Array.from(departments).sort();
  }

  /**
   * Toggle employee status
   */
  toggleEmployeeStatus(id: string): Observable<Employee> {
    const employee = this.employees().find(e => e.id === id);
    if (!employee) throw new Error('Employee not found');

    const newStatus = employee.status === 'active' ? 'inactive' : 'active';
    
    return this.http.patch<Employee>(`${this.API_URL}/employees/${id}/`, { status: newStatus })
      .pipe(
        tap({
          next: (updated) => {
            this.employees.update(employees => 
              employees.map(e => e.id === id ? updated : e)
            );
          }
        })
      );
  }
}
