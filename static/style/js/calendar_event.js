
// $(document).ready(function(){
// var calendar = $('#calendar').fullCalendar({
//     header: {
//         left: 'prev,next today',
//         center: 'title',
//         right: 'month,agendaWeek,agendaDay'
//     },
//     events:'/Admin/all_appointment/',
//            selectable: true,
//            selectHelper: true,
//            editable: true,
//            eventLimit: true,
//            select: function (start, end, allDay){
//             $('#eventModal').modal('show');
//             $('#saveEventBtn').on('click', function () {
               
//                 var title = $('#eventTitleInput').val();
//                 // var startdateTime = $('#startdate').val();
//                 // var enddateTime = $('#enddate').val();
                
                
//                 $('#eventModal').modal('hide');

//                 if (title) {
                    
//                     var start = $.fullCalendar.formatDate(start, "Y-MM-DD HH:mm:ss");
                   
//                     var end = $.fullCalendar.formatDate(end, "Y-MM-DD HH:mm:ss");
//                     $.ajax({
//                         type: "GET",
//                         url: '/Admin/add_appointment/',
//                         data: {'title': title,'start': start,'end':end},
//                         dataType: "json",
//                         success: function (data) {
//                             calendar.fullCalendar('refetchEvents');
//                             alert("Added Successfully");
//                         },
//                         error: function (data) {
//                             alert('There is a problem!!!');
//                         }
//                     });
//                 }
//             });
//         },
//     });
// });

// $(document).ready(function(){
//     var calendar = $('#calendar').fullCalendar({
//         header: {
//             left: 'prev,next today',
//             center: 'title',
//             right: 'month,agendaWeek,agendaDay'
//         },
//         events: '/Admin/all_appointment/',
//         selectable: true,
//         selectHelper: true,
//         editable: true,
//         eventLimit: true,
//         select: function (start, end, allDay) {
//             selectedStartDate = start;
//             $('#eventModal').modal('show');

//             $('#saveEventBtn').on('click', function () {
//                 console.log("workinggggggg")
//                 var title = $('#eventTitleInput').val();
//                 console.log("titleee", title)
//                 var time = $('#eventTime').val();
//                 console.log("time", time)
//                 var formattedStart = $.fullCalendar.formatDate(selectedStartDate, "Y-MM-DD");
//                 console.log("formattedStart", formattedStart);

//                 $('#eventModal').modal('hide');

//                 if (title) {
//                     $.ajax({
//                         type: "GET",
//                         url: '/Admin/add_appointment/',
//                         data: {'title': title, 'start': formattedStart, 'time': time},
//                         dataType: "json",
//                         success: function (data) {
//                             calendar.fullCalendar('refetchEvents');
//                             alert("Added Successfully");
//                         },
//                         error: function (xhr, status, error) {
//                             console.error('Error:', error);
//                             alert('There is a problem!!!');
//                         }
//                     });
//                 }
//             });
//         },
//         eventDrop: function (event) {
//             var start = $.fullCalendar.formatDate(event.start, "Y-MM-DD");
//             var end = $.fullCalendar.formatDate(event.end, "Y-MM-DD HH:mm:ss");
//             var title = event.title;
//             var id = event.id;
//             $.ajax({
//                 type: "GET",
//                 url: '/Admin/update',
//                 data: {'title': title, 'start': start,  'id': id},
//                 dataType: "json",
//                 success: function (data) {
//                     calendar.fullCalendar('refetchEvents');
//                     alert('Event Update');
//                 },
//                 error: function (data) {
//                     alert('There is a problem!!!');
//                 }
//             });
//         },

//         eventRender: function (event, element) {
//             // Customize the way events are rendered
//             element.find('.fc-title').html('<div class="event-title">' + event.title + '</div><div class="event-time">' + event.time + '</div>');
//         },
//     });
// });


$(document).ready(function(){
    var calendar = $('#calendar').fullCalendar({
        // header: {
        //     left: 'prev,next today',
        //     center: 'title',
        //     right: 'month,agendaWeek,agendaDay'
        // },
        events: '/Admin/all_appointment/',
        selectable: true,
        selectHelper: true,
        editable: true,
        eventLimit: true,
        select: function (start, end, allDay) {
            selectedStartDate = start;
            $('#eventModal').modal('show');

            $('#saveEventBtn').on('click', function () {
                
                var title = $('#eventTitleInput').val();
               
                var time = $('#eventTime').val();
                
                var formattedStart = $.fullCalendar.formatDate(selectedStartDate, "Y-MM-DD");
                

                $('#eventModal').modal('hide');

                if (title) {
                    $.ajax({
                        type: "GET",
                        url: '/Admin/add_appointment/',
                        data: {'title': title, 'start': formattedStart, 'time': time},
                        dataType: "json",
                        success: function (data) {
                            console.log('Data from the server:', data);
                            calendar.fullCalendar('refetchEvents');
                            alert("Added Successfully");
                        },
                        error: function (xhr, status, error) {
                            console.error('Error:', error);
                            alert('There is a problem!!!');
                        }
                    });
                }
            });
        },

        eventClick: function (event) {
               if (confirm("Are you sure you want to remove it?")) {
                   var id = event.id;
                   $.ajax({
                       type: "GET",
                       url: '/Admin/remove',
                       data: {'id': id},
                       dataType: "json",
                       success: function (data) {
                           calendar.fullCalendar('refetchEvents');
                           alert('Appointment Removed');
                       },
                       error: function (data) {
                           alert('There is a problem!!!');
                       }
                   });
               }
           },
        
        eventDrop: function (event) {
            var start = $.fullCalendar.formatDate(event.start, "Y-MM-DD");
            // var end = $.fullCalendar.formatDate(event.end, "Y-MM-DD HH:mm:ss");
            var title = event.title;
            var id = event.id;
            $.ajax({
                type: "GET",
                url: '/Admin/update/',
                data: {'title': title,'start':start,'id': id},
                dataType: "json",
                success: function (data) {
                    console.log('Data from the server:', data);
                    calendar.fullCalendar('refetchEvents');
                    alert('Appointment Update');
                },
                error: function (xhr, status, error) {
                    console.error('Error:', error);
                    alert('There is a problem!!!');
                }
            });
        },
        eventRender: function (event, element) {
            // Customize the way events are rendered
            element.find('.fc-title').html('<div class="event-title">' + event.title + '</div><div class="event-time">' + event.time + '</div>');
        },
    });
});
