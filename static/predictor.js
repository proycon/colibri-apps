candidates = [];
count = 0;
mode = 0; //0 = input, 1 = suggestions
select = 0;
stopchars = [" ",",",".","!",";",":","\n"];
maxcontextchars = 25;
seqnr = 0;
filter = "";

function showsuggestions(leftcontext, prefix) {
    s = "<span id=\"context\">" + leftcontext + "</span> <ol>";
    for (var i = 0; i < candidates.length; i++) {
        //p = Math.round(candidates[i].count / count);
        s += "<li class=\"candidate\" id=\"candidate" + (i +1) + "\">" + candidates[i].text;
        if (i < 9) {
            s += " <span>" + (i + 1) + "</span>";
        }
        s += "</li>";
        if (i > 20) break;
    }
    s += "</ol>";
    $('#suggestions').html(s);
}

function getcontext() { 
    var text = $('#textinput').val();

    var sel = $("#textinput").getSelection(); //current cursor position is an empty selection

    sel.start = sel.end - maxcontextchars;
    if (sel.start < 0) sel.start = 0;
    

    var leftcontext = text.replace("\n"," ").substr(sel.start,sel.end - sel.start);

    //do we have a filter? are we in the middle of typing a word?
    filter = "";
    for (var i = leftcontext.length; i > 0; i--) {
        if ($.inArray(leftcontext.charAt(i), stopchars) != -1) {
            leftcontext = leftcontext.substr(0,i);
            break;
        } else {
            filter = leftcontext.charAt(i) + filter;
        }
    }

    //prune leftcontext until the first spacing/punctuation char so we don't
    //have half-finished words at the beginning
    var begin = 0;
    for (var i = 0; i < leftcontext.length; i++) {
        if ($.inArray(leftcontext.charAt(i), stopchars) != -1) {
            begin = i + 1;
            break;
        }
    }
    leftcontext = leftcontext.substr(begin);

    return {'leftcontext': leftcontext.trim(), 'filter':filter.trim()}
}


function getsuggestions() {
    var data = getcontext();

    if (data.leftcontext.length > 0) {
        seqnr = seqnr + 1
        $.ajax({
            url: "predict/",
            type: "GET",
            dataType: "json",
            data: { 'context': data.leftcontext,  'filter': data.filter },
            seqnr: seqnr, 
            leftcontext: data['leftcontext'],
            success: function(result) {
                if (seqnr == this.seqnr) { //in case the call was slow and we typed ahead, ignore the results
                    candidates = result.candidates;
                    count = result.count;
                    showsuggestions(this.leftcontext, this.filter);
                }
            },
            error: function() {
                alert("Error");
            },
        });
    }
}

function selectsuggestion() {
    $('li.candidate').removeClass('selected');
    if (mode == 1) {
        $('li#candidate' + select).addClass("selected");
    }
}


function acceptsuggestion() {
    var sel = $("#textinput").getSelection(); //current cursor position is an empty selection
    if (filter != "") {
        //remove filter prior to adding the candidate
        $('#textinput').deleteText(sel.end- filter.length, sel.end, true);
        filter = "";
    }
    var sel2 = $("#textinput").getSelection(); //current cursor position is an empty selection
    $('#textinput').insertText( candidates[select-1].text, sel2.end, "collapseToEnd");
}

$(document).ready(function() {
    $("#textinput").keydown(function(event) {
        if (event.keyCode == 9) {
            //TAB
            if ((mode == 0) && (candidates.length > 0)) {
                mode = 1;
                select = 1;
                selectsuggestion();
            } else if (mode == 1) {
                select += 1;
                if (select > candidates.length) {
                    select = 1;
                }
                selectsuggestion();
            }
            event.preventDefault();
            return false; //override default behaviour
        } else if ((mode == 1) && ((event.keyCode == 13) || (event.keyCode == 32) || (event.keyCode == 190) || (event.keyCode == 188) || (event.keyCode == 186) || ((event.keyCode >= 49) && (event.keyCode <= 57))) ) { 
            //selection of 1-9
            if ((event.keyCode >= 49) && (event.keyCode <= 57)) {
                select = event.keyCode - 48;
            }
            selectsuggestion();
            acceptsuggestion();
            mode = 0;
            if ((event.keyCode >= 49) && (event.keyCode <= 57)) {
                var sel = $("#textinput").getSelection(); //current cursor position is an empty selection
                $('#textinput').insertText( " ", sel.end, "collapseToEnd");
                event.preventDefault();
                return false;
            }
        } else if ((event.keyCode == 27) && (mode == 1)) {
            mode = 0;
            selectsuggestion(); //will hide selection
            event.preventDefault();
            return false; //override default behaviour
        } 
    });


    $('#textinput').keyup(function(event) {
        if ((mode == 1) && (event.keyCode == 9)) {
            //ignore tabbing
        } else if ((event.keyCode < 10) || (event.keyCode > 27)) { //ignore control character, back to mode 0, get new suggestions
            mode = 0;
            selectsuggestion();
            getsuggestions();
        }
    });

});
