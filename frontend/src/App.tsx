import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import LoginPage from './pages/LoginPage';
import RoleDashboardPage from "./pages/RoleDashboardPage";
import EmployeeListPage from './pages/EmployeeListPage';
import EmployeeProfilePage from './pages/EmployeeProfilePage';
import AddEmployeePage from './pages/AddEmployeePage';
import EditEmployeePage from './pages/EditEmployeePage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailsPage from './pages/ProjectDetailsPage';
import DepartmentsPage from './pages/DepartmentsPage';
import RolesPage from './pages/RolesPage';
import SkillsPage from './pages/SkillsPage';
import ProtectedRoute from './router/ProtectedRoute';
import EnterprisePage from './pages/EnterprisePage';
export default function App()
    {return <Routes>
        <Route path="/login" element={<LoginPage/>}/>
        <Route element={<ProtectedRoute/>}>
        <Route element={<AppLayout/>}>
        <Route path="/dashboard" element={<RoleDashboardPage />} />
        <Route path="/attendance" element={<EnterprisePage module="attendance"/>}/>
        <Route path="/leave" element={<EnterprisePage module="leave"/>}/>
        <Route path="/payroll" element={<EnterprisePage module="payroll"/>}/>
        <Route path="/my-payroll" element={<EnterprisePage module="my-payroll"/>}/>
        <Route path="/audit" element={<EnterprisePage module="audit"/>}/>
        <Route path="/reports" element={<EnterprisePage module="audit"/>}/>
        <Route path="/settings" element={<EnterprisePage module="audit"/>}/>
        <Route path="/employees" element={<EmployeeListPage/>}/>
        <Route path="/employees/:id" element={<EmployeeProfilePage/>}/>
        <Route element={<ProtectedRoute allowedRoles={['ADMIN','HR']}/>}>
        <Route path="/employees/new" element={<AddEmployeePage/>}/>
        <Route path="/employees/:id/edit" element={<EditEmployeePage/>}/></Route>
        <Route path="/projects" element={<ProjectsPage/>}/>
        <Route path="/projects/:id" element={<ProjectDetailsPage/>}/>
        <Route path="/departments" element={<DepartmentsPage/>}/>
        <Route path="/roles" element={<RolesPage/>}/>
        <Route path="/skills" element={<SkillsPage/>}/></Route></Route>
        <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
    </Routes>}
