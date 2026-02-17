import Foundation

enum AgentMode {
    case coaching
    case onboarding

    var chatPath: String {
        switch self {
        case .coaching: return "chat"
        case .onboarding: return "onboarding-chat"
        }
    }

    var navTitle: String {
        switch self {
        case .coaching: return "Coaching Agent"
        case .onboarding: return "Onboarding Agent"
        }
    }

    var description: String {
        switch self {
        case .coaching:
            return "Jump into live coaching with your existing chat experience."
        case .onboarding:
            return "Start with a brief interview so we can tailor guidance to your family."
        }
    }
}

