import { api } from './api';
export const hrService={
 overview:()=>api.get<any>('/analytics/overview'),
 attendance:(params='')=>api.get<any[]>(`/attendance/today${params}`),
 leaves:(status='')=>api.get<any[]>(`/leave/requests${status?`?status=${status}`:''}`),
 leaveTypes:()=>api.get<any[]>('/leave/types'),
 decideLeave:(id:string,status:string)=>api.post(`/leave/requests/${id}/decision`,{status}),
 payrollOverview:()=>api.get<any>('/payroll/overview'),
 trend:(days:number=14)=>api.get<any[]>(`/analytics/trend?days=${days}`),
 departments:()=>api.get<any[]>('/analytics/departments'),
 payrollRecords:()=>api.get<any[]>('/payroll/records'),
myPayroll:()=>api.get<any[]>('/payroll/my'),
createLeave:(payload:any)=>api.post('/leave/requests',payload),
 createPayroll:(period:string)=>api.post('/payroll/runs',{period}),
 audit:()=>api.get<any[]>('/audit-logs'),
};
