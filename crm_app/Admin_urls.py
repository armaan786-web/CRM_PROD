from django.urls import path, include

from .AdminViews import *

urlpatterns = [
    path("Dashboard/", admin_dashboard.as_view(), name="admin_dashboard"),
    path("AddVisaCountry/", add_visacountry, name="add_visacountry"),
    path("VisaCountry/update/", visacountryupdate_view, name="visacountryupdate_view"),
    path("import/Country", import_country, name="importcountry"),
    path(
        "VisaCountry/Delete/<int:id>", delete_visa_country, name="delete_visa_country"
    ),
    path("AddVisaCategory/", add_visacategory, name="add_visacategory"),
    path("VisaCategory/Edit/", visacategoryupdate_view, name="visacategoryupdate_view"),
    path("deletecategory/<int:id>/", delete_category, name="delete_category"),
    path("AddDocumentCategory/", add_documentcategory, name="add_documentcategory"),
    path(
        "DocumentCategory/Edit/",
        documentcategoryupdate_view,
        name="documentcategoryupdate_view",
    ),
    path(
        "deletedocumentcategory/<int:id>/",
        delete_documentcategory,
        name="delete_documentcategory",
    ),
    path("AddDocument/", add_document, name="add_document"),
    path("Document/Edit/", documentupdate_view, name="documentupdate_view"),
    path("deletedocument/<int:id>/", delete_document, name="delete_document"),
    path(
        "AddCaseCategoryDocument/",
        CaseCategoryDocumentCreateView.as_view(),
        name="add_CaseCategoryDocument",
    ),
    path(
        "CaseCategoryDocumentList/",
        CaseCategoryDocumentListView.as_view(),
        name="CaseCategoryDocument_list",
    ),
    path(
        "CaseCategoryDocumentEdit/<int:pk>",
        editCaseCategoryDocument.as_view(),
        name="editCaseCategoryDocument",
    ),
    path(
        "casecategorydocument/delete/<int:id>/",
        delete_casecategorydocument,
        name="delete_casecategorydocument",
    ),
    path("Addbranch/", add_branch, name="add_branch"),
    path("Branch/Edit/", branchupdate_view, name="branchupdate_view"),
    path("deletebranch/<int:id>/", delete_branch, name="delete_branch"),
    path("import/Branch", import_branch, name="import_branch"),
    path("create_group/", CreateGroupView.as_view(), name="create_group"),
    path("GroupList/", GroupListView.as_view(), name="Group_list"),
    path("GroupEdit/<int:pk>", editGroup.as_view(), name="editgroup"),
    path("group/delete/<int:id>/", delete_group, name="delete_group"),
    path("personal_details/", PersonalDetailsView.as_view(), name="personal_details"),
    path("receiver_details/", ReceiverDetailsView.as_view(), name="receiver_details"),
    path(
        "ViewCourierAddress/", viewcourieraddress_list, name="viewcourieraddress_list"
    ),
    path(
        "update_company_details/<int:id>/",
        UpdateCompanyDetailsView.as_view(),
        name="update_company_details",
    ),
    path(
        "update_receiver_details/<int:id>/",
        UpdateReceiverDetailsView.as_view(),
        name="update_receiver_details",
    ),
    path(
        "courierdetails/delete/<int:id>/",
        delete_courierdetails,
        name="delete_courierdetails",
    ),
    path("emp_personal_details/", add_employee, name="emp_personal_details"),
    path("emp_list/", all_employee.as_view(), name="emp_list"),
    path("Employe/Update/<int:pk>", employee_update, name="employee_update"),
    path("Employe/Update/Save", employee_update_save, name="employee_update_save"),
    path("Employee/delete/<int:id>/", delete_employee, name="delete_employee"),
    path("add_agent/", add_agent, name="add_agent"),
    path("agent_list/", all_agent.as_view(), name="agent_list"),
    path("agent_grid/", Grid_agent.as_view(), name="agent_grid"),
    path("agent_delete/<int:id>/", agent_delete, name="agent_delete"),
    path("Agent/Details/<int:id>", admin_agent_details, name="admin_agent_details"),
    path(
        "Agent/Agreement/<int:id>", admin_agent_agreement, name="admin_agent_agreement"
    ),
    path(
        "Agent/Agreement/update/<int:id>/",
        admin_agent_agreement_update,
        name="update_agreement",
    ),
    path(
        "Agent/Agreement/Delete/<int:id>/",
        admin_agent_agreement_delete,
        name="admin_agent_agreement_delete",
    ),
    path("Agent/Kyc/<int:id>", admin_agent_kyc, name="admin_agent_kyc"),
    path("Agent/Kyc/Delete/<int:id>", admin_agent_delete, name="admin_agent_delete"),
    path(
        "AllOutSourceAgent/", all_outsource_agent.as_view(), name="all_outsource_agent"
    ),
    path(
        "OutSourceAgent/Details/<int:id>",
        admin_outsourceagent_details,
        name="admin_outsourceagent_details",
    ),
    path(
        "OutSourceAgent/Agreement/<int:id>",
        admin_outsource_agent_agreement,
        name="admin_outsource_agent_agreement",
    ),
    path(
        "OutSource/Agent/Kyc/<int:id>",
        admin_outsource_agent_kyc,
        name="admin_outsource_agent_kyc",
    ),
    path(
        "Outsourceagent_delete/<int:id>/",
        outstsourceagent_delete,
        name="outstsourceagent_delete",
    ),
    path(
        "OutsourceAgent/Agreement/update/<int:id>/",
        admin_outsourceagent_agreement_update,
        name="admin_outsourceagent_agreement_update",
    ),
    path(
        "OutsourceAgent/Agreement/Delete/<int:id>/",
        admin_outsource_agent_agreement_delete,
        name="admin_outsource_agent_agreement_delete",
    ),
    path(
        "gridOutSourceAgent/",
        Grid_outsource_agent.as_view(),
        name="grid_outsource_agent",
    ),
    path("AddPackage/", PackageCreateView.as_view(), name="add_Package"),
    path("PackageList/", PackageListView.as_view(), name="Package_list"),
    path("PackageEdit/<int:pk>", editPackage.as_view(), name="editPackage"),
    path("packages/<int:pk>/", PackageDetailView.as_view(), name="package_detail"),
    path("packages/<int:id>/apply/", PackageApplyView, name="package_apply"),
    path("package/delete/<int:id>/", delete_package, name="delete_package"),
    path("LoginLogs", loginlog.as_view(), name="loginlog"),
    path("AddSubCategory/", add_subcategory, name="add_subcategory"),
    path("SubCategoryList/", subcategory_list, name="subcategory_list"),
    path(
        "SubCategoryEdit/<int:id>", visa_subcategory_edit, name="visa_subcategory_edit"
    ),
    path("pricing/delete/<int:id>/", delete_pricing, name="delete_pricing"),
    path("ChangePassword", ChangePassword, name="ChangePassword"),
    path("AddEnquiry/", Enquiry1View.as_view(), name="enquiry_form1"),
    path("AddEnquiry2/", Enquiry2View.as_view(), name="enquiry_form2"),
    path("AddEnquiry3/", Enquiry3View.as_view(), name="enquiry_form3"),
    path("enquiry_form4/<int:id>/", admindocument, name="enquiry_form4"),
    path("Uploaddocument/", upload_document, name="uploaddocument"),
    path("Delete/UploadFile/<int:id>", delete_docfile, name="docfile"),
    # ------------------------------ Package Leads -------------------
    path("PacAddEnquiry/", PackageEnquiry1View, name="packageenquiry_form1"),
    path("PacAddEnquiry2/", PackageEnquiry2View, name="packageenquiry_form2"),
    path("PacAddEnquiry3/", PackageEnquiry3View, name="packageenquiry_form3"),
    # ------------------------------- LEADS ------------------------
    path("AllNewLeads", admin_new_leads_details, name="admin_new_leads_details"),
    path("AllGridLeads", admin_grid_leads_details, name="admin_grid_leads_details"),
    path("AddNotes/", add_notes, name="add_notes"),
    path("delete_and_archive/<int:id>/", delete_and_archive, name="delete_and_archive"),
    path("restore/<int:id>/", restore, name="restore"),
    path("ArchiveList/", ArchiveListView.as_view(), name="Archive_list"),
    path("EnrolledLeads/", enrolled_Application.as_view(), name="Enrolled_leads"),
    path(
        "EnrolledGridLeads/",
        enrolledGrid_Application.as_view(),
        name="EnrolledGrid_leads",
    ),
    path(
        "edit/Enrolled/Application/<int:id>",
        edit_enrolled_application,
        name="edit_enrolled_application",
    ),
    path("Educaion/Summary/<int:id>", combined_view, name="education_summary"),
    path("Test/Score/Delete/<int:id>", delete_test_score, name="delete_test_score"),
    path("Product/<int:id>", editproduct_details, name="edit_product_details"),
    path("enrolled_document/<int:id>/", enrolleddocument, name="enrolled_document"),
    path(
        "enrolledUploaddocument/",
        enrolled_upload_document,
        name="enrolleduploaddocument",
    ),
    path(
        "Delete/enrolledUploadFile/<int:id>",
        enrolled_delete_docfile,
        name="enrolleddocfile",
    ),
    path("logout", admin_logout, name="admin_logout"),
    path("activity_logs/", activity_log_view, name="activity_logs"),
    path("AddQueries/", FAQCreateView.as_view(), name="Admin_addfaq"),
    path(
        "resolved-queries/",
        ResolvedFAQListView.as_view(),
        name="Admin_resolved_queries",
    ),
    path(
        "pending-queries/", PendingFAQListView.as_view(), name="Admin_pending_queries"
    ),
    path("add_answer/", FAQUpdateView, name="add_answer"),
    path("delete_query/<int:id>", delete_query, name="delete_query"),
    path("Profile/", profileview.as_view(), name="admin_profile"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("PreEnrolled/<int:id>", leadupated, name="leadupated"),
    # ---------------------------------- chat group -------------------
    path("chatgroup/", CreateChatGroupView.as_view(), name="chatgroup"),
    path("chatgroupList/", ChatGroupListView.as_view(), name="ChatGroup_list"),
    path("chatgroupEdit/<int:pk>", editGroupChat.as_view(), name="EditChatGroup"),
    path(
        "chatgroup/delete/<int:id>/",
        chat_group_delete_group,
        name="chat_group_delete_group",
    ),
    path(
        "UpdateAssign/<int:id>", update_assigned_employee, name="update_assign_employee"
    ),
    path("lead_update/<int:id>", admin_lead_updated, name="admin_lead_updated"),
    path("Enq/Appointment/Save", admin_appointment_Save, name="admin_appointment_Save"),
    path(
        "Enq/Appointment/Done/<int:id>/",
        admin_appointment_done,
        name="admin_appointment_done",
    ),
    path("approve_product/<int:id>/", approve_product, name="approve_product"),
    path("disapprove_product/<int:id>/", disapprove_product, name="disapprove_product"),
    path("Successstory_list/", add_successstory, name="Successstory_list"),
    path(
        "Successstory_Delete/<int:id>/", delete_successstory, name="Successstory_Delete"
    ),
    path("News_list/", add_news, name="News_list"),
    path("News_Delete/<int:id>/", delete_news, name="News_Delete"),
    # -----------------------------------------
    path(
        "switch-to-outsource/<int:agent_id>/",
        switch_to_outsource_agent,
        name="switch_to_outsource",
    ),
    path("reportlist/", ReportList.as_view(), name="reportlist"),
    path("email_template/", email_template, name="email_template"),
    path(
        "UpdateAssignAgent/<int:id>",
        update_assigned_agent,
        name="update_assigned_agent",
    ),
    path("UpdateAssignOP/<int:id>", update_assigned_op, name="update_assigned_op"),
    path(
        "Disapprove_PackageList/",
        DisapprivePackageListView.as_view(),
        name="Disapprove_Package_list",
    ),
    path("color_code/<int:id>", color_code, name="color_code"),
    path("Appointment/", admin_appointment, name="admin_appointment"),
    path("update_news/", NewsUpdateView, name="update_news"),
    path("all_appointment/", all_appointment, name="all_appointment"),
    path("add_appointment/", add_appointment, name="add_appointment"),
    path("update/", update, name="update"),
    path("remove/", remove, name="remove"),
    path("Todo/", add_todo, name="add_todo"),
    path("Update/Todo/<int:id>/", update_todo, name="update_todo"),
    path("Delete/Todo/<int:id>/", delete_todo, name="delete_todo"),
    # ------------------------ Download Zip ---------------------
    path(
        "download_all_documents/<int:id>/",
        download_all_documents,
        name="admin_download_all_documents",
    ),
    path("search_enquiries/", search_enquiries, name="search_enquiries"),
    path("search_employee/", search_employee, name="search_employee"),
    path("visateam_color/", visa_team_color, name="visa_team_color"),
    path("color_employee_list/", color_employee_list, name="color_employee_list"),
    path("team_updated/", visateamcolorupdate_view, name="team_updated"),
]
