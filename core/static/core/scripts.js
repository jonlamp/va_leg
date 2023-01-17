$('.collapse-head').click(function(){
    tgt = $(this).attr("data-target");
    console.log(tgt)
    $("#"+tgt).slideToggle();
})