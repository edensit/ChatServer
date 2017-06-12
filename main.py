import server


def main():
    try:
        chat_server = server.ChatServer()
        chat_server.run()
    except Exception as error:
        import traceback
        print "Error!"
        print "Error message: %s" % error
        print "Traceback:"
        traceback.print_exc()
        print "Press return to exit.."
        raw_input()
    

if __name__ == '__main__':
    main()
