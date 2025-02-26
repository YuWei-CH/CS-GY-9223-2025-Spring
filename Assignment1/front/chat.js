var checkout = {};

$(document).ready(function () {
  var $messages = $(".messages-content"),
    d, h, m,
    i = 0;

  var apiUrl = "https://jzqolf7dtj.execute-api.us-east-1.amazonaws.com/lambda0/chat"; // Your API Gateway URL
  
  // Generate a session ID in cookie
  function getSessionId() {
    let sessionId = localStorage.getItem("session_id");
    if (!sessionId) {
      sessionId = "sess-" + Math.random().toString(36).substr(2, 9);
      localStorage.setItem("session_id", sessionId);
    }
    return sessionId;
  }
  // Store sessionId
  var sessionId = getSessionId();

  $(window).on("load", function () {
    $messages.mCustomScrollbar();
    insertResponseMessage("Hi there, I'm your personal Concierge. How can I help?");
  });

  function updateScrollbar() {
    $messages.mCustomScrollbar("update").mCustomScrollbar("scrollTo", "bottom", {
      scrollInertia: 10,
      timeout: 0,
    });
  }

  function setDate() {
    d = new Date();
    if (m != d.getMinutes()) {
      m = d.getMinutes();
      $('<div class="timestamp">' + d.getHours() + ":" + m + "</div>").appendTo($(".message:last"));
    }
  }

  
  function callChatbotApi(message) {
    return fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            session_id: sessionId, // return sessionID in JSON
            messages: [
                {
                    type: "unstructured",
                    unstructured: {
                        id: new Date().getTime().toString(),
                        text: message,
                        timestamp: new Date().toISOString(),
                    },
                },
            ],
        }),
    })
    // Debug print
    .then((response) => {
        console.log("Raw API Response:", response);
        return response.json();
    })
    .then((data) => {
        console.log("Parsed API Response:", data);

        // Check data type, ensure it is a string
        if (typeof data === "string") {
            console.log("Manually parsing `data` since it is a string.");
            data = JSON.parse(data);
        }

        return data;
    })
    .catch((error) => {
        console.error("API Error:", error);
        return { messages: [{ type: "unstructured", unstructured: { text: "Oops, something went wrong. Please try again." } }] };
    });
}

  function insertMessage() {
    let msg = $(".message-input").val();
    if ($.trim(msg) == "") {
        return false;
    }
    $('<div class="message message-personal">' + msg + "</div>").appendTo($(".mCSB_container")).addClass("new");
    setDate();
    $(".message-input").val(null);
    updateScrollbar();

    callChatbotApi(msg)
      .then((data) => {
          console.log("Processing API Response:", data);

          // Add debugging log to check `messages`
          if (data && "messages" in data) {
              console.log("Found `messages` in response:", data.messages);
          } else {
              console.log("`messages` field is missing");
          }

          // Fix condition to ensure `messages` is recognized
          if (data && data.messages && Array.isArray(data.messages) && data.messages.length > 0) {
              for (var message of data.messages) {
                  console.log("Message Object:", message);
                  if (message.type === "unstructured" && message.unstructured) {
                      insertResponseMessage(message.unstructured.text);
                  } else {
                      insertResponseMessage("Unexpected response format.");
                  }
              }
          } else {
              console.log("No messages found in response:", data);
              insertResponseMessage("No response received.");
          }
    })
    .catch((error) => {
        console.log(" Error occurred:", error);
        insertResponseMessage("Oops, something went wrong. Please try again.");
    });
  }
  $(".message-submit").click(function () {
    insertMessage();
  });

  $(window).on("keydown", function (e) {
    if (e.which == 13) {
      insertMessage();
      return false;
    }
  });

  function insertResponseMessage(content) {
    $('<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>').appendTo($(".mCSB_container"));
    updateScrollbar();

    setTimeout(function () {
      $(".message.loading").remove();
      $('<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' + content + "</div>").appendTo($(".mCSB_container")).addClass("new");
      setDate();
      updateScrollbar();
      i++;
    }, 500);
  }
});