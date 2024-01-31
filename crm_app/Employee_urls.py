from django.urls import path, include
from .EmployeeViews import *

urlpatterns = [
    path("Dashboard/", employee_dashboard.as_view(), name="employee_dashboard"),
    path("AddEnquiry/", emp_Enquiry1View.as_view(), name="emp_enquiry_form1"),
    path("AddEnquiry2/", emp_Enquiry2View.as_view(), name="emp_enquiry_form2"),
    path("AddEnquiry3/", emp_Enquiry3View.as_view(), name="emp_enquiry_form3"),
    path("enquiry_form4/<int:id>/", empdocument, name="emp_enquiry_form4"),
    path("Uploaddocument/", emp_upload_document, name="emp_upload_document"),
    path("Delete/UploadFile/<int:id>", emp_delete_docfile, name="emp_delete_docfile"),
    # -----------------------------------
    path(
        "Employee/PacAddEnquiry/", empPackageEnquiryForm1, name="empPackageEnquiryForm1"
    ),
    path(
        "Employee/PacAddEnquiry2/",
        empPackageEnquiry2View,
        name="emp_packageenquiry_form2",
    ),
    path(
        "Employee/PacAddEnquiry3/",
        emp_PackageEnquiry3View,
        name="emp_packageenquiry_form3",
    ),
    path("Lead/List/", employee_lead_list, name="employee_lead_list"),
    path("Lead/Grid/", employee_lead_grid, name="employee_lead_grid"),
    path("Enrollled/Lead/", employee_enrolled_lead, name="employee_enrolled_lead"),
    path("Enrollled/Grid/", employee_enrolled_grid, name="employee_enrolled_grid"),
    # ------------------------------ Add lead staging --------------------------
    path("PreEnrolled/Save/<int:id>/", preenrolled_save, name="preenrolled_save"),
    path("Active/Save/<int:id>/", active_save, name="active_save"),
    path("Enrolled/Save/<int:id>/", enrolled_save, name="enrolled_save"),
    path("Enprocess/Save/<int:id>/", enprocess_save, name="enprocess_save"),
    path(
        "Ready_to_submit/Save/<int:id>/",
        ready_to_submit_save,
        name="ready_to_submit_save",
    ),
    path(
        "appointment_save/Save/<int:id>/",
        appointment_save,
        name="appointment_save",
    ),
    path(
        "ready_to_collection_save/Save/<int:id>/",
        ready_to_collection_save,
        name="ready_to_collection_save",
    ),
    path(
        "result_save/Save/<int:id>/",
        result_save,
        name="result_save",
    ),
    path(
        "delivery_Save/Save/<int:id>/",
        delivery_Save,
        name="delivery_Save",
    ),
    path("Reject/Save/<int:id>/", reject_save, name="reject_save"),
    path("Enq/Appointment/Save", enq_appointment_Save, name="enq_appointment_Save"),
    path(
        "Enq/Appointment/Done/<int:id>/",
        appointment_done,
        name="appointment_done",
    ),
    path("AddNotes/", emp_add_notes, name="emp_add_notes"),
    # ------------------------------------------- Agent ----------------------------------------
    path("add_agent/", emp_add_agent, name="emp_add_agent"),
    path("agent_list/", emp_all_agent.as_view(), name="emp_agent_list"),
    path("agent_Grid/", emp_allGrid_agent.as_view(), name="emp_agent_grid"),
    path("agent_delete/<int:id>/", employee_agent_delete, name="employee_agent_delete"),
    path("Agent/Details/<int:id>", emp_agent_details, name="emp_agent_details"),
    path(
        "Agent/Agreement/<int:id>",
        employee_agent_agreement,
        name="employee_agent_agreement",
    ),
    path(
        "Agent/Agreement/update/<int:id>/",
        employee_agent_agreement_update,
        name="employee_agent_agreement_update",
    ),
    path(
        "Agent/Agreement/Delete/<int:id>/",
        emp_agent_agreement_delete,
        name="emp_agent_agreement_delete",
    ),
    path("Agent/Kyc/<int:id>", emp_agent_kyc, name="emp_agent_kyc"),
    # ----------------------------- Out Source Agent -----------------------------
    path(
        "AllOutSourceAgent/",
        emp_all_outsource_agent.as_view(),
        name="emp_all_outsource_agent",
    ),
    path(
        "AllOutSourceAgentGrid/",
        emp_allGrid_outsource_agent.as_view(),
        name="emp_allgrid_outsource_agent",
    ),
    path(
        "Outsourceagent_delete/<int:id>/",
        emp_outstsourceagent_delete,
        name="emp_outstsourceagent_delete",
    ),
    path(
        "OutSourceAgent/Details/<int:id>",
        emp_outsourceagent_details,
        name="emp_outsourceagent_details",
    ),
    path(
        "OutSourceAgent/Agreement/<int:id>",
        emp_outsource_agent_agreement,
        name="emp_outsource_agent_agreement",
    ),
    path(
        "OutsourceAgent/Agreement/update/<int:id>/",
        emp_outsourceagent_agreement_update,
        name="emp_outsourceagent_agreement_update",
    ),
    path(
        "OutsourceAgent/Agreement/Delete/<int:id>/",
        emp_outsource_agent_agreement_delete,
        name="emp_outsource_agent_agreement_delete",
    ),
    path(
        "OutsourceAgent/Kyc/<int:id>",
        emp_outsource_agent_kyc,
        name="emp_outsource_agent_kyc",
    ),
    # ------------------------------------------------- Enrolled -------------------------
    path(
        "edit/Enrolled/Application/<int:id>",
        emp_edit_enrolled_application,
        name="emp_edit_enrolled_application",
    ),
    path("Educaion/Summary/<int:id>", emp_combined_view, name="emp_education_summary"),
    path("Product/<int:id>", emp_editproduct_details, name="emp_editproduct_details"),
    path(
        "enrolled_document/<int:id>/", emp_enrolleddocument, name="emp_enrolleddocument"
    ),
    path(
        "enrolledUploaddocument/",
        emp_enrolled_upload_document,
        name="emp_enrolled_upload_document",
    ),
    path(
        "Delete/enrolledUploadFile/<int:id>",
        emp_enrolled_delete_docfile,
        name="emp_enrolled_delete_docfile",
    ),
    # --------------------------------Follow Up-----------------------------
    path("Followup", followup, name="followup"),
    path("FollowupList/", emp_followup_list, name="emp_followup_list"),
    path("Followup/Delete/<int:id>", emp_followup_delete, name="emp_followup_delete"),
    path("followupupdate/", followup_update, name="followupupdate"),
    path("logout", employee_logout, name="employee_logout"),
    path("ChangePassword", ChangePassword, name="EmployeeChangePassword"),
    #  --------------------------------- FaQ -------------------------
    path("AddQueries/", emp_FAQCreateView.as_view(), name="emp_FAQCreateView"),
    path(
        "resolved-queries/",
        ResolvedFAQListView.as_view(),
        name="Emp_resolved_queries",
    ),
    path("pending-queries/", PendingFAQListView.as_view(), name="Emp_pending_queries"),
    path("emp_add_answer/", FAQUpdateView, name="emp_add_answer"),
    path("PackageList/", PackageListView.as_view(), name="Employee_Package_list"),
    path(
        "packages/<int:pk>/",
        PackageDetailView.as_view(),
        name="employee_package_detail",
    ),
    path("packages/<int:id>/apply/", empPackageApply, name="empPackageApply"),
    path("Employee/profile", profileview.as_view(), name="Employee_profile"),
    path("Employee/edit_profile/", edit_profile, name="edit_employee_profile"),
    # --------------------------------------------------------------------------
    path("AddVisaCountry/", add_visacountry, name="emp_add_visacountry"),
    path(
        "VisaCountry/update/", visacountryupdate_view, name="emp_visacountryupdate_view"
    ),
    path("import/Country", import_country, name="emp_importcountry"),
    path(
        "VisaCountry/Delete/<int:id>",
        delete_visa_country,
        name="emp_delete_visa_country",
    ),
    path("AddVisaCategory/", add_visacategory, name="emp_add_visacategory"),
    path(
        "VisaCategory/Edit/",
        visacategoryupdate_view,
        name="emp_visacategoryupdate_view",
    ),
    path("deletecategory/<int:id>/", delete_category, name="emp_delete_category"),
    path("AddDocumentCategory/", add_documentcategory, name="emp_add_documentcategory"),
    path(
        "DocumentCategory/Edit/",
        documentcategoryupdate_view,
        name="emp_documentcategoryupdate_view",
    ),
    path(
        "deletedocumentcategory/<int:id>/",
        delete_documentcategory,
        name="emp_delete_documentcategory",
    ),
    path("AddDocument/", add_document, name="emp_add_document"),
    path("Document/Edit/", documentupdate_view, name="emp_documentupdate_view"),
    path("deletedocument/<int:id>/", delete_document, name="emp_delete_document"),
    path(
        "AddCaseCategoryDocument/",
        CaseCategoryDocumentCreateView.as_view(),
        name="emp_add_CaseCategoryDocument",
    ),
    path(
        "CaseCategoryDocumentList/",
        CaseCategoryDocumentListView.as_view(),
        name="emp_CaseCategoryDocument_list",
    ),
    path(
        "CaseCategoryDocumentEdit/<int:pk>",
        editCaseCategoryDocument.as_view(),
        name="emp_editCaseCategoryDocument",
    ),
    path(
        "casecategorydocument/delete/<int:id>/",
        delete_casecategorydocument,
        name="emp_delete_casecategorydocument",
    ),
    path("Addbranch/", add_branch, name="emp_add_branch"),
    path("Branch/Edit/", branchupdate_view, name="emp_branchupdate_view"),
    path("deletebranch/<int:id>/", delete_branch, name="emp_delete_branch"),
    path("import/Branch", import_branch, name="emp_import_branch"),
    path("create_group/", CreateGroupView.as_view(), name="emp_create_group"),
    path("GroupList/", GroupListView.as_view(), name="emp_Group_list"),
    path("GroupEdit/<int:pk>", editGroup.as_view(), name="emp_editgroup"),
    path("group/delete/<int:id>/", delete_group, name="emp_delete_group"),
    path(
        "personal_details/",
        PersonalDetailsView.as_view(),
        name="employee_personal_details",
    ),
    path(
        "receiver_details/",
        ReceiverDetailsView.as_view(),
        name="employee_receiver_details",
    ),
    path(
        "ViewCourierAddress/",
        viewcourieraddress_list,
        name="emp_viewcourieraddress_list",
    ),
    path(
        "update_company_details/<int:id>/",
        UpdateCompanyDetailsView.as_view(),
        name="emp_update_company_details",
    ),
    path(
        "update_receiver_details/<int:id>/",
        UpdateReceiverDetailsView.as_view(),
        name="emp_update_receiver_details",
    ),
    path(
        "courierdetails/delete/<int:id>/",
        delete_courierdetails,
        name="emp_delete_courierdetails",
    ),
    path("emp_personal_details/", add_employee, name="emp_emp_personal_details"),
    path("emp_list/", all_employee.as_view(), name="emp_emp_list"),
    path("Employe/Update/<int:pk>", employee_update, name="emp_employee_update"),
    path("Employe/Update/Save", employee_update_save, name="emp_employee_update_save"),
    path("Employee/delete/<int:id>/", delete_employee, name="emp_delete_employee"),
    path("AddSubCategory/", add_subcategory, name="emp_add_subcategory"),
    path("SubCategoryList/", subcategory_list, name="emp_subcategory_list"),
    path(
        "SubCategoryEdit/<int:id>",
        visa_subcategory_edit,
        name="emp_visa_subcategory_edit",
    ),
    path("pricing/delete/<int:id>/", delete_pricing, name="emp_delete_pricing"),
    path("AddPackage/", PackageCreateView.as_view(), name="Emp_Package"),
    path("News_list/", NewsList.as_view(), name="Emp_News_list"),
    path("Success_StoryList/", SuccessStoryList.as_view(), name="Emp_SuccessStoryList"),
    path("Appointment/", emp_appointment, name="emp_appointment"),
    path("all_appointment/", all_appointment, name="emp_all_appointment"),
    path("add_appointment/", add_appointment, name="emp_add_appointment"),
    path("update/", update, name="update"),
    path("remove/", remove, name="remove"),
    # ------------------------- Todo List -------------------------
    path("Todo/", emp_add_todo, name="emp_add_todo"),
    path("Update/Todo/<int:id>/", emp_update_todo, name="emp_update_todo"),
    path("Delete/Todo/<int:id>/", emp_delete_todo, name="emp_delete_todo"),
    # ---------------------------- download zip -------------------------
    path("Employee_color_code/", color_code, name="Employee_color_code"),
    path(
        "download_all_documents/<int:id>/",
        download_all_documents,
        name="download_all_documents",
    ),
    path("search_enquiries/", search_enquiries, name="Emp_search_enquiries"),
    path("NewLead/Save/", submit, name="newlead_save"),
    path("lead_add_agent/", lead_emp_add_agent, name="lead_emp_add_agent"),
]
