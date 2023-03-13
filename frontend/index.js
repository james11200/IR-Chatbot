const types = ["Education", "Techonology", "Politics", "Healthcare", "Environment"]
user_utterances = []
bot_utterances = []
context = ''

document.addEventListener("DOMContentLoaded", () => {
	const inputField = document.getElementById("input")
    inputField.addEventListener("keydown", function(e) {
        if (e.code === "Enter") {
            let input = inputField.value;
            inputField.value = "";
            output(input);
    }
  });
});

function output(input) {
	addChat(input);
}

function onLoad() {
  for (let type of types){
    addCheck(type);
  }
}

function addCheck(subject) {
  // name of checkbox
  var name = document.createTextNode(subject)
  var checkbox = document.createElement("Input");
  checkbox.setAttribute("type", "checkbox");

  // line break
  br = document.createElement("br")
  checkbox.checked = false;

  // add to html
  document.body.appendChild(name);
  document.body.appendChild(checkbox);
  document.body.appendChild(br)
  checkbox.setAttribute("name", subject)
  checkbox.setAttribute("id", subject)
}

function addChat(input) {
  //get div and put users text into it
  const mainDiv = document.getElementById("main");
  let userDiv = document.createElement("div");
  userDiv.id = "user";
  userDiv.innerHTML = `You: <span id="user-response">${input}</span>`;
  user_utterances.push(input)
  mainDiv.appendChild(userDiv);

  let botDiv = document.createElement("div");
  botDiv.id = "bot";
  // query
  hit_api(input).then((response)=> response.json()).then((data) => {
    botDiv.innerHTML = `Chatbot: <span id="bot-response">${data['response']}</span>`
    context = data['post']
    bot_utterances.push(data['response'])
  })

//  botDiv.innerHTML = `Chatbot: <span id="bot-response">${out}</span>`;
  mainDiv.appendChild(botDiv);
}


async function hit_api(query) {
  const url = "http://127.0.0.1:5000/bot/";
  var resp;
  user_topics = [];
  for (let topic of types) {
    box = document.getElementById(topic);
    if (box.checked) {user_topics.push(topic); }
  }
  return await fetch(url, {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
      },
      method : 'POST',
      body: JSON.stringify({'query' : query, 'context' : context, 'topics': user_topics, 'bot_utterances' : bot_utterances, 'user_utterances' : user_utterances}),
      })
}