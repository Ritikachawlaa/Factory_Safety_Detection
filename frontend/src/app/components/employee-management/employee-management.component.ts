import { Component, computed, inject, signal } from '@angular/core';
import { EmployeeService, Employee, EmployeeCreateRequest } from '../../services/employee.service';

@Component({
  selector: 'app-employee-management',
  templateUrl: './employee-management.component.html',
  styleUrls: ['./employee-management.component.css']
})
export class EmployeeManagementComponent {
  private employeeService = inject(EmployeeService);

  // Signals
  employees = this.employeeService.employees;
  isLoading = this.employeeService.isLoading;
  error = this.employeeService.error;
  
  showAddModal = signal(false);
  showEditModal = signal(false);
  selectedEmployee = signal<Employee | null>(null);
  searchQuery = signal('');
  selectedDepartment = signal<string>('all');
  selectedFile = signal<File | null>(null);
  previewUrl = signal<string | null>(null);

  // Form fields
  formData = signal({
    employeeId: '',
    name: '',
    email: '',
    phone: '',
    department: '',
    designation: '',
    joiningDate: ''
  });

  // Computed values
  filteredEmployees = computed(() => {
    let result = this.employees();
    
    // Filter by search query
    const query = this.searchQuery().toLowerCase();
    if (query) {
      result = result.filter(emp =>
        emp.name.toLowerCase().includes(query) ||
        emp.employeeId.toLowerCase().includes(query) ||
        emp.email.toLowerCase().includes(query)
      );
    }
    
    // Filter by department
    const dept = this.selectedDepartment();
    if (dept !== 'all') {
      result = result.filter(emp => emp.department === dept);
    }
    
    return result;
  });

  departments = computed(() => {
    const depts = new Set(this.employees().map(e => e.department));
    return ['all', ...Array.from(depts).sort()];
  });

  totalEmployees = computed(() => this.employees().length);
  activeEmployees = computed(() => 
    this.employees().filter(e => e.status === 'active').length
  );

  // ============================================================================
  // MODAL METHODS
  // ============================================================================

  openAddModal(): void {
    this.resetForm();
    this.showAddModal.set(true);
  }

  openEditModal(employee: Employee): void {
    this.selectedEmployee.set(employee);
    this.formData.set({
      employeeId: employee.employeeId,
      name: employee.name,
      email: employee.email,
      phone: employee.phone,
      department: employee.department,
      designation: employee.designation,
      joiningDate: employee.joiningDate
    });
    this.previewUrl.set(employee.photoUrl);
    this.showEditModal.set(true);
  }

  closeModals(): void {
    this.showAddModal.set(false);
    this.showEditModal.set(false);
    this.resetForm();
  }

  resetForm(): void {
    this.formData.set({
      employeeId: '',
      name: '',
      email: '',
      phone: '',
      department: '',
      designation: '',
      joiningDate: ''
    });
    this.selectedFile.set(null);
    this.previewUrl.set(null);
    this.selectedEmployee.set(null);
  }

  // ============================================================================
  // FILE UPLOAD
  // ============================================================================

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB');
        return;
      }
      
      this.selectedFile.set(file);
      
      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        this.previewUrl.set(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  }

  // ============================================================================
  // CRUD OPERATIONS
  // ============================================================================

  createEmployee(): void {
    const data = this.formData();
    const file = this.selectedFile();
    
    if (!file) {
      alert('Please upload an employee photo');
      return;
    }
    
    if (!this.validateForm(data)) {
      return;
    }
    
    const request: EmployeeCreateRequest = {
      ...data,
      photo: file
    };
    
    this.employeeService.createEmployee(request).subscribe({
      next: () => {
        alert('✅ Employee created successfully!');
        this.closeModals();
      },
      error: (err) => {
        alert('❌ Failed to create employee: ' + err.message);
      }
    });
  }

  updateEmployee(): void {
    const employee = this.selectedEmployee();
    if (!employee) return;
    
    const data = this.formData();
    const file = this.selectedFile();
    
    if (!this.validateForm(data)) {
      return;
    }
    
    const request: Partial<EmployeeCreateRequest> = {
      ...data,
      ...(file && { photo: file })
    };
    
    this.employeeService.updateEmployee(employee.id, request).subscribe({
      next: () => {
        alert('✅ Employee updated successfully!');
        this.closeModals();
      },
      error: (err) => {
        alert('❌ Failed to update employee: ' + err.message);
      }
    });
  }

  deleteEmployee(employee: Employee): void {
    if (!confirm(`Are you sure you want to delete ${employee.name}?`)) {
      return;
    }
    
    this.employeeService.deleteEmployee(employee.id).subscribe({
      next: () => {
        alert('✅ Employee deleted successfully!');
      },
      error: (err) => {
        alert('❌ Failed to delete employee: ' + err.message);
      }
    });
  }

  toggleStatus(employee: Employee): void {
    this.employeeService.toggleEmployeeStatus(employee.id).subscribe({
      next: () => {
        const newStatus = employee.status === 'active' ? 'inactive' : 'active';
        alert(`✅ Employee status changed to ${newStatus}`);
      },
      error: (err) => {
        alert('❌ Failed to update status: ' + err.message);
      }
    });
  }

  // ============================================================================
  // VALIDATION
  // ============================================================================

  validateForm(data: any): boolean {
    if (!data.employeeId || !data.name || !data.email || !data.phone || !data.department || !data.designation || !data.joiningDate) {
      alert('Please fill in all required fields');
      return false;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
      alert('Please enter a valid email address');
      return false;
    }
    
    // Validate phone format (Indian format)
    const phoneRegex = /^[6-9]\d{9}$/;
    if (!phoneRegex.test(data.phone.replace(/\D/g, ''))) {
      alert('Please enter a valid 10-digit phone number');
      return false;
    }
    
    return true;
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  getStatusBadgeClass(status: string): string {
    return status === 'active' 
      ? 'bg-green-500 text-white' 
      : 'bg-gray-500 text-white';
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  }
}
